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
import shutil
import subprocess
import sys
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


def install_loader() -> int:
    """Splice scripts/bashrc-loader.sh into ~/.bashrc between its markers,
    proving every byte outside them unchanged (padme, 2026-09-29). Bytes, not
    text: CRLF and non-UTF-8 lines must survive as they are."""
    rc_file = Path(os.environ["HOME"]) / ".bashrc"
    block = (REPO / "scripts" / "bashrc-loader.sh").read_bytes()
    old = rc_file.read_bytes() if rc_file.exists() else b""
    manual = (f"  remove the old harness loader block(s) from {rc_file} by hand "
              f"(each ends at `|| _idh_stubs`), then rerun idh install")
    try:
        span = _span(old)
    except ValueError as exc:
        print(f"idh: loader NOT installed: {rc_file}: {exc}\n{manual}", file=sys.stderr)
        return 1
    base = old
    if span is None:
        if b"_idh_refuse" in old or b"_idh_unreachable" in old:
            print(f"idh: loader NOT installed: {rc_file} holds a pre-marker "
                  f"loader block\n{manual}", file=sys.stderr)
            return 1
        base += b"\n" if old and not old.endswith(b"\n") else b""
        span = (len(base), len(base))
    if base[span[0]:span[1]] == block:
        return 0
    backup = rc_file.with_name(f".bashrc.idh-bak-{time.strftime('%Y%m%dT%H%M%S')}")
    backup.write_bytes(old)
    outside = (base[: span[0]], base[span[1]:])
    rc_file.write_bytes(outside[0] + block + outside[1])
    new = rc_file.read_bytes()
    kept = _span(new)
    if kept is None or (new[: kept[0]], new[kept[1]:]) != outside:
        rc_file.write_bytes(old)
        print(f"idh: loader splice altered lines outside the markers; {rc_file} "
              f"restored from {backup}", file=sys.stderr)
        return 1
    print(f"installed: loader block in {rc_file} (previous copy: {backup})")
    return 0


TIMER = "idh-mammoth-audit.timer"


def install_timers() -> int:
    """Install the one unit pair versioned in systemd/. claude-refresh and
    claude-telemetry-prune are not ours yet (0985/0986)."""
    if not shutil.which("systemctl"):
        print("timers skipped: no systemctl on PATH")
        return 0
    config = os.environ.get("XDG_CONFIG_HOME") or Path(os.environ["HOME"]) / ".config"
    units = Path(config) / "systemd" / "user"
    units.mkdir(parents=True, exist_ok=True)
    for unit in ("idh-mammoth-audit.service", TIMER):
        shutil.copyfile(REPO / "systemd" / unit, units / unit)
    for argv in (["daemon-reload"], ["enable", "--now", TIMER]):
        if subprocess.run(["systemctl", "--user", *argv]).returncode:
            print(f"idh: systemctl --user {' '.join(argv)} failed", file=sys.stderr)
            return 1
    print(f"enabled: {TIMER}")
    return 0


def install() -> int:
    return install_links() | install_loader() | install_timers()


def _git(*args):
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def distance():
    """(ahead, behind) of HEAD against its upstream, as of the last fetch."""
    counts = _git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    return tuple(int(n) for n in counts.split()) if counts else None


def sync() -> int:
    """sync-local-main.sh unchanged: it fast-forwards, or names what blocks."""
    run = subprocess.run([str(REPO / "scripts" / "sync-local-main.sh"), str(REPO)],
                         capture_output=True, text=True)
    print(run.stdout, end="")
    # The script always exits 0 (it serves hooks); its words carry the verdict.
    if any(w in run.stdout for w in ("skipped", "left untouched", "refused", "could not")):
        print("idh sync: the checkout was not synced (see above)", file=sys.stderr)
        return 1
    gap = distance()
    if gap is None:
        print("idh sync: no upstream to compare with", file=sys.stderr)
        return 1
    if gap[1]:
        print(f"idh sync: still {gap[1]} commit(s) behind upstream", file=sys.stderr)
        return 1
    return 0


def status() -> int:
    """Installed vs declared, timer state, distance to origin."""
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
    timer = "no systemctl"
    if shutil.which("systemctl"):
        run = subprocess.run(["systemctl", "--user", "is-enabled", TIMER],
                             capture_output=True, text=True)
        timer = run.stdout.strip() or "unknown"
    print(f"timer    {TIMER}: {timer}")
    gap = distance()
    print("origin   no upstream" if gap is None
          else f"origin   ahead {gap[0]}, behind {gap[1]} (as of the last fetch)")
    print(f"declared {len(listed)}, " + ", ".join(f"{k} {n}" for k, n in tally.items()))
    return 1 if tally["broken"] else 0


def main(argv) -> int:
    command, *rest = argv
    try:
        if command == "check":
            return check(*rest[:1])
        if command in ("sync", "status"):
            return globals()[command]()
        return install()
    except V.ManifestError as exc:
        print(f"idh: adapters/projections.json is unusable: {exc}", file=sys.stderr)
        return 1
