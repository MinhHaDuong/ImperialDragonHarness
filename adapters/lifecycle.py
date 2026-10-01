"""Harness lifecycle on one machine: `idh install | check | status | sync` (0987).

The operator's command, not the runtimes': hooks and skills keep calling
scripts by path. adapters/projections.json is the one list of links, so
install creates exactly what check verifies, and the launch validator
(scripts/validate-projections.py) supplies the per-entry verdict. Links are
built from the structured `path`/`target` fields only; the free-form
`installer` text is display, never executed. Stdlib only, Python 3.12.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _validator():
    spec = importlib.util.spec_from_file_location(
        "validate_projections", REPO / "scripts" / "validate-projections.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _validator()


def root() -> Path:
    """The checkout spelled ~/.idh when the pointer reaches it, so links stay
    relocatable; the resolved checkout otherwise (first install)."""
    pointer = Path(os.environ["HOME"]) / ".idh"
    return pointer if V.resolved(pointer) == REPO else REPO


def entries(runtime=None):
    return V.load_entries(REPO / "adapters" / "projections.json", runtime)


def report(kind, detail, repair) -> None:
    print(f"  {kind}: {detail}\n    repair: {repair}", file=sys.stderr)


def install_links() -> int:
    """Create each absent entry; leave correct ones; refuse anything else."""
    rc = 0
    for entry in entries():
        base = root()  # re-read: once ~/.idh exists, later links go through it
        path, target = V.expand(entry["path"], base), V.expand(entry["target"], base)
        try:
            if not path.is_symlink() and not path.exists():
                if not entry["required"] and V.resolved(target) is None:
                    continue  # optional, and nothing to point at on this machine
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target)
                print(f"installed: {path} -> {target}")
                continue
        except OSError as exc:  # e.g. a regular file where a parent dir belongs
            report("REFUSED", f"{path}: {exc}", "inspect the path, then rerun idh install")
            rc = 1
            continue
        problem = V.check_entry(entry, base)
        if problem:
            report(*problem)
            rc = 1
    return rc


def check(runtime=None) -> int:
    failures = [p for e in entries(runtime) if (p := V.check_entry(e, root()))]
    for problem in failures:
        report(*problem)
    print(f"idh check: {len(failures)} broken" if failures else "idh check: ok")
    return 1 if failures else 0


BEGIN, END = b"# >>> Imperial Dragon Harness loader", b"# <<< Imperial Dragon Harness loader"


def _span(text: bytes):
    """(start, end) offsets of the one marked block, None when absent; raises
    ValueError when the markers do not delimit exactly one block."""
    start = text.find(BEGIN)
    if start < 0:
        return None
    end = text.find(END, start)
    if end < 0:
        raise ValueError("begin marker without an end marker")
    stop = text.find(b"\n", end)
    stop = len(text) if stop < 0 else stop + 1
    if text.find(BEGIN, stop) >= 0:
        raise ValueError("more than one loader block")
    return start, stop


def _fill(fd: int, data: bytes, mode: int) -> None:
    """Set `mode` (the source's, never wider), write every byte, fsync."""
    os.fchmod(fd, mode)
    view = memoryview(data)
    while view:  # os.write may write less than asked
        view = view[os.write(fd, view):]
    os.fsync(fd)


def _write_new(path: Path, fd: int, data: bytes, mode: int) -> None:
    """Fill a freshly created file; on any failure remove it, since a
    partial copy of ~/.bashrc may hold secrets."""
    try:
        try:
            _fill(fd, data, mode)
        finally:
            os.close(fd)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _backup(dest: Path, data: bytes, mode: int) -> Path:
    """O_EXCL with a counter: two installs in one second keep both copies."""
    stem = dest.with_name(f"{dest.name}.idh-bak-{time.strftime('%Y%m%dT%H%M%S')}")
    for n in range(1000):
        path = stem if n == 0 else stem.with_name(f"{stem.name}.{n}")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        _write_new(path, fd, data, mode)
        return path
    raise FileExistsError(f"no free backup name beside {stem}")


def _replace(dest: Path, data: bytes, mode: int) -> None:
    """Atomic rewrite: a unique 0600 temp file beside dest, filled, renamed
    over; any failure removes the temp file."""
    prefix = "." + dest.name.lstrip(".") + ".idh-tmp-"  # hidden, never "..bashrc"
    fd, name = tempfile.mkstemp(dir=dest.parent, prefix=prefix)
    tmp = Path(name)
    _write_new(tmp, fd, data, mode)
    try:
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def install_loader() -> int:
    """Splice scripts/bashrc-loader.sh into ~/.bashrc between its markers,
    proving every byte outside them unchanged (padme, 2026-09-29). Bytes, not
    text: CRLF and non-UTF-8 lines must survive as they are. A symlinked
    ~/.bashrc is rewritten at its target."""
    rc_file = Path(os.environ["HOME"]) / ".bashrc"
    try:
        return _splice(Path(os.path.realpath(rc_file)))
    except OSError as exc:
        print(f"idh: loader NOT installed: {exc}", file=sys.stderr)
        return 1


def _splice(dest: Path) -> int:
    block = (REPO / "scripts" / "bashrc-loader.sh").read_bytes()
    exists = dest.exists() or dest.is_symlink()
    if exists and not os.access(dest, os.W_OK):
        raise PermissionError(f"{dest} is not writable; left as it is")
    old = dest.read_bytes() if exists else b""
    mode = dest.stat().st_mode & 0o7777 if exists else 0o600
    manual = (f"  remove the old harness loader block(s) from {dest} by hand "
              f"(each ends at `|| _idh_stubs`), then rerun idh install")
    try:
        span = _span(old)
    except ValueError as exc:
        print(f"idh: loader NOT installed: {dest}: {exc}\n{manual}", file=sys.stderr)
        return 1
    base = old
    if span is None:
        if b"_idh_refuse" in old or b"_idh_unreachable" in old:
            print(f"idh: loader NOT installed: {dest} holds a pre-marker "
                  f"loader block\n{manual}", file=sys.stderr)
            return 1
        base += b"\n" if old and not old.endswith(b"\n") else b""
        span = (len(base), len(base))
    if base[span[0]:span[1]] == block:
        return 0
    backup = _backup(dest, old, mode) if exists else None
    outside = (base[: span[0]], base[span[1]:])
    _replace(dest, outside[0] + block + outside[1], mode)
    new = dest.read_bytes()
    kept = _span(new)
    if kept is None or (new[: kept[0]], new[kept[1]:]) != outside:
        _replace(dest, old, mode)
        print(f"idh: loader splice altered lines outside the markers; {dest} "
              f"restored (copy: {backup})", file=sys.stderr)
        return 1
    print(f"installed: loader block in {dest} (previous copy: {backup})")
    return 0



def install() -> int:
    # Both steps run; the exit code is non-zero when either refuses.
    return install_links() | install_loader()


def _git(*args):
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def distance():
    """(ahead, behind) of HEAD against its upstream, as of the last fetch."""
    counts = _git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    return tuple(int(n) for n in counts.split()) if counts else None


def sync() -> int:
    """Run sync-local-main.sh unchanged; it fast-forwards the local default
    branch (main) or names what blocks it. Success means that branch now
    equals its origin counterpart, whatever branch HEAD is on."""
    script = REPO / "scripts" / "sync-local-main.sh"
    try:
        run = subprocess.run([str(script), str(REPO)], capture_output=True, text=True)
    except OSError as exc:
        print(f"idh sync: cannot run {script}: {exc}", file=sys.stderr)
        return 1
    print(run.stdout, end="")
    # The script always exits 0 (it serves hooks); its words carry the verdict.
    if any(w in run.stdout for w in ("skipped", "left untouched", "refused", "could not")):
        print("idh sync: the checkout was not synced (see above)", file=sys.stderr)
        return 1
    # The branch the script chose: origin/HEAD's, else main, else master.
    head = _git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if head:
        branch = head.split("/", 1)[1]
    else:
        has_main = _git("show-ref", "--verify", "--quiet", "refs/heads/main") is not None
        branch = "main" if has_main else "master"
    behind = _git("rev-list", "--count", f"refs/heads/{branch}..refs/remotes/origin/{branch}")
    if behind is None:
        print(f"idh sync: cannot compare {branch} with origin/{branch}", file=sys.stderr)
        return 1
    if behind != "0":
        print(f"idh sync: {branch} still {behind} commit(s) behind origin/{branch}",
              file=sys.stderr)
        return 1
    return 0


def status() -> int:
    """Installed vs declared, distance to origin."""
    base, listed, tally = root(), entries(), {"ok": 0, "absent": 0, "broken": 0}
    for entry in listed:
        path, target = V.expand(entry["path"], base), V.expand(entry["target"], base)
        problem = V.check_entry(entry, base)
        if problem:
            state = problem[0]
        else:
            state = "ok" if path.is_symlink() or path.exists() else "absent"
        tally["broken" if problem else state] += 1
        print(f"{state:8} {path} -> {target}")
    gap = distance()
    print("origin   no upstream" if gap is None
          else f"origin   ahead {gap[0]}, behind {gap[1]} (as of the last fetch)")
    print(f"declared {len(listed)}, " + ", ".join(f"{k} {n}" for k, n in tally.items()))
    return 1 if tally["broken"] else 0


def main(argv) -> int:
    command, *rest = argv or [""]
    try:
        if command == "check":
            return check(*rest[:1])
        if command in ("install", "sync", "status") and not rest:
            return globals()[command]()
    except V.ManifestError as exc:
        print(f"idh: adapters/projections.json is unusable: {exc}", file=sys.stderr)
        return 1
    print(f"idh: unknown command {' '.join(argv)!r}", file=sys.stderr)
    return 2
