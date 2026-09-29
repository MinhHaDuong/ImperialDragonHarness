"""Move the harness checkout out of Claude Code's native root, and back (0985).

`idh relocate harness` is the cutover; `idh relocate harness --rollback` undoes
it. Before: the checkout is Claude Code's native root and ~/.idh points at it.
After: the checkout is ~/.idh, and the native root is a real directory holding
Claude Code's own state plus one link per harness entry the runtime reads (adapters/
cutover-layout.json). adapters/projections.json is rewritten for that layout and
`idh install` then creates exactly the links `idh check` verifies.

Both directions are idempotent and resumable: every mutation is one step of a
plan written to a journal before the first of them, and each step checks where
things are before acting, so a crash anywhere is finished by a rerun of either
direction. Both refuse before mutating on a dirty tree, an unclassified file,
a link that names the old root, or a name collision.

Guards: HOME must not be the account's real home unless --live is given (the
live window is ticket 0986); without --live, timer calls must stay inside the
disposable HOME (XDG_RUNTIME_DIR under it, no foreign session bus), so a
rehearsal can never pause the live timers. IDH_CUTOVER_CRASH_AT=N exits hard
(status 99) just before the Nth mutation: the rehearsal's crash-point test.
Stdlib only, Python 3.12.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LAYOUT = "adapters/cutover-layout.json"
MANIFEST = "adapters/projections.json"


class Refusal(Exception):
    pass


_done = 0


def checkpoint() -> None:
    """Called before every mutation; the crash hook for the rehearsal."""
    global _done
    _done += 1
    if os.environ.get("IDH_CUTOVER_CRASH_AT") == str(_done):
        os._exit(99)


def slug(path) -> str:
    """Claude Code's project-store key (0984): non-alphanumerics become '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def home_refusal(home: Path, account_home: Path, live: bool):
    """Why HOME may not be acted on, or None."""
    real = os.path.realpath(home) == os.path.realpath(account_home)
    if real and not live:
        return (f"HOME={home} is this account's real home. The live cutover is the "
                f"quiet-window step (ticket 0986): pass --live there, never here.")
    if live and not real:
        return f"--live given, but HOME={home} is not this account's home"
    return None


def timer_refusal(env, home: Path, live: bool):
    """Without --live, systemctl --user must not be able to reach a manager
    outside the disposable HOME."""
    if live or not shutil.which("systemctl", path=env.get("PATH")):
        return None
    runtime = env.get("XDG_RUNTIME_DIR")
    if not runtime or not os.path.realpath(runtime).startswith(os.path.realpath(home) + os.sep):
        return ("XDG_RUNTIME_DIR is not inside the disposable HOME, so systemctl --user "
                "could pause another session's timers; point it at a directory under HOME")
    bus = env.get("DBUS_SESSION_BUS_ADDRESS", "")
    if bus and str(os.path.realpath(home)) not in bus:
        return "DBUS_SESSION_BUS_ADDRESS names a bus outside the disposable HOME; unset it"
    return None


def _git(repo: Path, *args) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    r = subprocess.run(["git", "-C", str(repo), *args], env=env,
                       capture_output=True, text=True)
    if r.returncode:
        raise Refusal(f"git {' '.join(args)} failed in {repo}: {r.stderr.strip()}")
    return r.stdout


def _dirty(repo: Path) -> list:
    out = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    return [item[3:] for item in out.split("\0") if item]


def _is_checkout(p: Path) -> bool:
    return p.is_dir() and not p.is_symlink() and (p / ".git").is_dir()


def _write(path: Path, data: bytes, mode=None) -> None:
    """Atomic replace, keeping the file's mode (or `mode` for a new file)."""
    if mode is None:
        mode = path.stat().st_mode & 0o7777 if path.exists() else 0o600
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.idh-tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            os.fchmod(f.fileno(), mode)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _match(name: str, patterns) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


class Machine:
    def __init__(self, home: Path):
        self.home = home
        layout = json.loads((REPO / LAYOUT).read_text())
        self.layout = layout
        self.old = home / layout["native_root"]
        self.new = home / layout["checkout"]
        state = os.environ.get("XDG_STATE_HOME") or str(home / ".local" / "state")
        self.state = Path(state) / "idh" / "cutover"
        self.journal_file = self.state / "journal.json"

    # --- journal ---------------------------------------------------------

    def load(self):
        try:
            return json.loads(self.journal_file.read_text())
        except FileNotFoundError:
            return None

    def save(self, j) -> None:
        checkpoint()
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        _write(self.journal_file, (json.dumps(j, indent=2) + "\n").encode(), 0o600)

    def saved(self, name) -> bytes:
        return (self.state / name).read_bytes()

    def side(self, s: str) -> Path:
        """Plan paths: "c" is the checkout (at ~/.idh once moved), "n" the
        new native root."""
        return self.new if s == "c" else self.old

    # --- mapping ----------------------------------------------------------

    def native(self, name: str) -> bool:
        return _match(name, self.layout["native"])

    def remap_slug(self, s: str, forward=True) -> str:
        a, b = slug(self.old), slug(self.new)
        a, b = (a, b) if forward else (b, a)
        return b + s[len(a):] if s == a or s.startswith(a + "-") else s

    def remap_path(self, p: str) -> str:
        """A path in the checkout, re-rooted at ~/.idh; native paths stay."""
        old = str(self.old)
        if p == old:
            return str(self.new)
        if p.startswith(old + "/"):
            rest = p[len(old) + 1:]
            if not self.native(rest.split("/")[0]):
                return f"{self.new}/{rest}"
        return p

    # --- preflight ----------------------------------------------------------

    def preflight(self, env) -> dict:
        old, new, layout = self.old, self.new, self.layout
        if not _is_checkout(old):
            raise Refusal(f"{old} is not the harness checkout (no .git directory)")
        if os.path.lexists(new) and not (new.is_symlink() and new.resolve() == old.resolve()):
            raise Refusal(f"{new} exists and is not the pointer to {old}")
        if str(self.state.resolve()).startswith(str(old.resolve()) + os.sep):
            raise Refusal(f"the journal directory {self.state} lies inside {old}")
        if dirty := _dirty(old):
            raise Refusal("the checkout has uncommitted changes; commit or remove them: "
                          + ", ".join(dirty[:10]))
        tracked = {p.split("/")[0] for p in _git(old, "ls-files", "-z").split("\0") if p}
        missing = [n for n in layout["claude_links"] if n not in tracked]
        if missing:
            raise Refusal(f"claude_links names untracked entries: {', '.join(missing)}")
        names = sorted(os.listdir(old))
        unknown = [n for n in names if n != ".git" and n not in tracked
                   and not _match(n, layout["keep"]) and not self.native(n)]
        if unknown:
            raise Refusal(f"unclassified entries in {old}: {', '.join(unknown)}; list each in "
                          f"{LAYOUT} as keep or native before the cutover")

        # Links declared in the manifest must not name the old root: they
        # would dangle once the checkout moves. Spelled through ~/.idh they survive.
        manifest = json.loads((old / MANIFEST).read_text())
        stale = []
        for e in manifest["entries"]:
            p = Path(str(new) + e["path"][len("$IDH_ROOT"):]) if e["path"].startswith(
                "$IDH_ROOT") else Path(str(self.home) + e["path"][1:])
            if p.is_symlink() and p != new:
                text = os.readlink(p)
                if text == str(old) or text.startswith(str(old) + "/"):
                    stale.append(f"{p} -> {text}")
        if stale:
            raise Refusal("links name the old root and would dangle: " + "; ".join(stale)
                          + " (relink them through ~/" + layout["checkout"] + ")")

        ops = [["mkdir", "n", "", old.stat().st_mode & 0o7777]]
        ops += [["move", "c", n, "n", n] for n in names if self.native(n)]
        memory = []
        projects = old / "projects"
        if projects.is_dir():
            ops.append(["mkdir", "n", "projects", projects.stat().st_mode & 0o7777])
            for s in sorted(os.listdir(projects)):
                ns = self.remap_slug(s)
                if ns != s and os.path.lexists(projects / ns):
                    raise Refusal(f"{projects / s} would be renamed onto the existing {ns}")
                ops.append(["move", "c", f"projects/{s}", "n", f"projects/{ns}"])
                mem = projects / s / "memory"
                if mem.is_dir() and not mem.is_symlink():
                    ops.append(["mkdir", "c", f"projects/{ns}",
                                (projects / s).stat().st_mode & 0o7777])
                    ops.append(["move", "n", f"projects/{ns}/memory", "c", f"projects/{ns}/memory"])
                    memory.append(ns)

        pre = (old / MANIFEST).read_bytes()
        post, links = self.post_manifest(manifest, memory)
        claude_json = self.home / ".claude.json"
        keys = {}
        if claude_json.exists():
            projects_keys = json.loads(claude_json.read_bytes()).get("projects", {})
            keys = {k: self.remap_path(k) for k in projects_keys if self.remap_path(k) != k}
            clash = [v for v in keys.values() if v in projects_keys]
            if clash:
                raise Refusal(f"~/.claude.json already has projects keyed {', '.join(clash)}")
        worktrees = []
        wt_dir = old / ".git" / "worktrees"
        for gitdir in sorted(wt_dir.glob("*/gitdir")) if wt_dir.is_dir() else []:
            path = gitdir.read_text().strip().removesuffix("/.git")
            worktrees.append([path, self.remap_path(path)])

        timers = []
        if shutil.which("systemctl", path=env.get("PATH")):
            for t in self.layout["timers"]:
                r = subprocess.run(["systemctl", "--user", "is-active", t],
                                   capture_output=True, text=True)
                if r.stdout.strip() == "active":
                    timers.append(t)

        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        _write(self.state / "pre-projections.json", pre, 0o600)
        _write(self.state / "post-projections.json", post, 0o600)
        if claude_json.exists():
            _write(self.state / "pre-claude.json", claude_json.read_bytes(), 0o600)
        return {
            "state": "cutting",
            "old": str(old), "new": str(new),
            "idh_link": os.readlink(new) if new.is_symlink() else None,
            "ops": ops, "next": 0, "links": links, "timers": timers,
            "claude_json_keys": keys, "worktrees": worktrees,
            "manifest": {"pre": sha(pre), "post": sha(post)},
            "claude_json": {"pre": sha(claude_json.read_bytes()) if claude_json.exists()
                            else None, "post": None},
        }

    def post_manifest(self, manifest, memory):
        """Swap the whole-root entry for one entry per projected harness entry."""
        root = self.layout["native_root"]
        out, links = [], []
        for e in manifest["entries"]:
            if e["path"] != f"~/{root}":
                out.append(e)
                continue
            for name in self.layout["claude_links"]:
                out.append({"path": f"~/{root}/{name}", "target": f"$IDH_ROOT/{name}",
                            "runtimes": ["claude"], "required": True,
                            "why": "Claude Code reads it from its native root; "
                                   "projected per entry since the cutover (0985)"})
            for s in memory:
                out.append({"path": f"~/{root}/projects/{s}/memory",
                            "target": f"$IDH_ROOT/projects/{s}/memory",
                            "runtimes": ["claude"], "required": True,
                            "why": "tracked project memory; Claude Code keys it by the "
                                   "resolved cwd and follows the link (0984)"})
        for e in out:
            if e["path"].startswith(f"~/{root}/"):
                links.append(e["path"][len(f"~/{root}/"):])
        return dump_manifest(manifest["_comment"], out), links

    # --- steps -------------------------------------------------------------

    def move(self, src: Path, dst: Path, strict=True) -> None:
        """Rename unless already done. Undoing the step the journal marks as
        maybe-reached passes strict=False: it may never have run."""
        if os.path.lexists(src) and not os.path.lexists(dst):
            checkpoint()
            os.rename(src, dst)
        elif os.path.lexists(src):
            raise Refusal(f"both {src} and {dst} exist; resolve by hand, then rerun")
        elif strict and not os.path.lexists(dst):
            raise Refusal(f"neither {src} nor {dst} exists: the journal and the disk disagree")

    def timers(self, j, verb) -> None:
        for t in j["timers"]:
            checkpoint()
            r = subprocess.run(["systemctl", "--user", verb, t])
            if r.returncode:
                raise Refusal(f"systemctl --user {verb} {t} failed")
            print(f"{'paused' if verb == 'stop' else 'resumed'}: {t}")

    def repair_worktrees(self, j, forward=True) -> None:
        repo = self.new if forward else self.old
        paths = [p[1] if forward else p[0] for p in j["worktrees"]]
        paths = [p for p in paths if os.path.isdir(p)]
        if paths:
            checkpoint()
            _git(repo, "worktree", "repair", *paths)
            print(f"repaired: {len(paths)} worktree(s)")
        # git leaves a .git file alone when it still resolves, and it does
        # through the restored ~/.idh link; spell it as it was spelled before.
        for p in paths:
            dotgit = Path(p) / ".git"
            text = dotgit.read_text()
            want = f"gitdir: {repo}/.git/worktrees/{text.strip().rsplit('/', 1)[-1]}\n"
            if text != want:
                checkpoint()
                _write(dotgit, want.encode())

    def rekey(self, j, forward=True) -> None:
        path = self.home / ".claude.json"
        if not path.exists() or not j["claude_json_keys"]:
            return
        raw = path.read_bytes()
        marks = j["claude_json"]
        if forward:
            if sha(raw) == marks["post"]:
                return
            data = json.loads(raw)
            data["projects"] = {j["claude_json_keys"].get(k, k): v
                                for k, v in data.get("projects", {}).items()}
            out = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
            marks["post"] = sha(out)
            self.save(j)  # the mark first: a crash after the write still finds it
        elif sha(raw) == marks["pre"]:
            return
        elif sha(raw) == marks["post"]:
            out = self.saved("pre-claude.json")
        else:  # edited since the cutover: undo the re-key only
            back = {v: k for k, v in j["claude_json_keys"].items()}
            data = json.loads(raw)
            data["projects"] = {back.get(k, k): v for k, v in data.get("projects", {}).items()}
            out = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
            print("~/.claude.json changed since the cutover: keys restored, bytes not")
        checkpoint()
        _write(path, out)
        print(f"re-keyed: {len(j['claude_json_keys'])} project(s) in ~/.claude.json")

    def idh(self, *args) -> int:
        return subprocess.run([sys.executable, str(self.new / "bin" / "idh"), *args]).returncode

    # --- directions -------------------------------------------------------

    def cutover(self, env) -> int:
        j = self.load()
        if j and j["state"] == "rolling-back":
            raise Refusal("a rollback is half done; finish it: idh relocate harness --rollback")
        if j and j["state"] == "cut":
            print(f"already cut over: the checkout is {self.new}")
            rc = self.idh("check")
            self.timers(j, "start")
            return rc
        if j is None:
            j = self.preflight(env)
            self.save(j)
        self.timers(j, "stop")
        if self.new.is_symlink() and _is_checkout(self.old):
            checkpoint()
            self.new.unlink()
        if _is_checkout(self.old) and not os.path.lexists(self.new):
            checkpoint()
            os.rename(self.old, self.new)
            print(f"moved: {self.old} -> {self.new}")
        if not _is_checkout(self.new):
            raise Refusal(f"the checkout is at neither {self.old} nor {self.new}")
        # `next` is saved before each step: every step below it is done, the
        # step at it may be, none above it is. Rollback reverses only up to it.
        for i in range(j["next"], len(j["ops"])):
            j["next"] = i
            self.save(j)
            op = j["ops"][i]
            if op[0] == "mkdir":
                p = self.side(op[1]) / op[2]
                if not os.path.lexists(p):
                    checkpoint()
                    p.mkdir()
                    p.chmod(op[3])
            else:
                self.move(self.side(op[1]) / op[2], self.side(op[3]) / op[4])
        if j["next"] < len(j["ops"]):
            j["next"] = len(j["ops"])
            self.save(j)
        print(f"split: {sum(op[0] == 'move' for op in j['ops'])} move(s) into {self.old}")
        manifest = self.new / MANIFEST
        if sha(manifest.read_bytes()) != j["manifest"]["post"]:
            checkpoint()
            _write(manifest, self.saved("post-projections.json"))
            print(f"rewrote: {MANIFEST} for the per-entry layout")
        self.rekey(j)
        self.repair_worktrees(j)
        if self.idh("install") or self.idh("check"):
            raise Refusal("idh install or idh check failed after the move (see above); timers "
                          "stay paused. Repair, or undo: idh relocate harness --rollback")
        j["state"] = "cut"
        self.save(j)
        self.timers(j, "start")
        print(f"cutover complete: the checkout is {self.new}; "
              f"undo with: idh relocate harness --rollback")
        return 0

    def rollback(self) -> int:
        j = self.load()
        if j is None:
            if _is_checkout(self.old) and self.new.is_symlink():
                print(f"nothing to roll back: the checkout is {self.old}")
                return 0
            raise Refusal(f"no cutover journal in {self.state}, and {self.old} is not the "
                          f"checkout: nothing this command can safely undo")
        if j["state"] != "rolling-back":
            j["state"] = "rolling-back"
            self.save(j)
        self.timers(j, "stop")
        self.rekey(j, forward=False)
        if _is_checkout(self.new):
            # The cutover's own changes: the manifest, and the project dirs
            # it renamed (tracked memory under the old and the new slug).
            own = [f"projects/{op[i].split('/')[1]}/" for op in j["ops"]
                   if op[0] == "move" and op[2].startswith("projects/") for i in (2, 4)]
            foreign = [p for p in _dirty(self.new)
                       if p != MANIFEST and not p.startswith(tuple(own))]
            if foreign:
                raise Refusal("the checkout has changes the cutover did not make; commit or "
                              "remove them first: " + ", ".join(foreign[:10]))
            manifest = self.new / MANIFEST
            now = sha(manifest.read_bytes())
            if now == j["manifest"]["post"]:
                checkpoint()
                _write(manifest, self.saved("pre-projections.json"))
            elif now != j["manifest"]["pre"]:
                raise Refusal(f"{MANIFEST} changed since the cutover; restore it by hand")
            for rel in j["links"]:
                p = self.old / rel
                if p.is_symlink():
                    checkpoint()
                    p.unlink()
            # Same bookkeeping as the cutover's `next`: a project dir that keeps
            # its slug returns to the very path a step reads, so a finished
            # step must never be replayed.
            steps = list(reversed(j["ops"][: j["next"] + 1]))
            swept = False
            for i in range(j.get("undo", 0), len(steps)):
                j["undo"] = i
                self.save(j)
                op = steps[i]
                if op[0] == "move":
                    self.move(self.side(op[3]) / op[4], self.side(op[1]) / op[2], strict=False)
                else:
                    if op[1] == "n" and not swept:
                        self.sweep()
                        swept = True
                    p = self.side(op[1]) / op[2]
                    if p.is_dir() and not p.is_symlink():
                        left = sorted(os.listdir(p))
                        if left:
                            raise Refusal(f"{p} still holds {', '.join(left[:10])}; "
                                          f"move them out, then rerun")
                        checkpoint()
                        p.rmdir()
            checkpoint()
            os.rename(self.new, self.old)
            print(f"moved: {self.new} -> {self.old}")
        if _is_checkout(self.old) and not os.path.lexists(self.new) and j["idh_link"]:
            checkpoint()
            self.new.symlink_to(j["idh_link"])
        self.repair_worktrees(j, forward=False)
        self.timers(j, "start")
        checkpoint()
        self.state.rename(self.state.with_name(f"cutover.rolled-back-{time.strftime('%Y%m%dT%H%M%S')}"))
        print(f"rollback complete: the checkout is {self.old}")
        return 0

    def sweep(self) -> None:
        """Native files created in the new root since the cutover go back with
        the rest; anything unclassified is refused, never moved by guess."""
        projects = self.old / "projects"
        if projects.is_dir():
            for s in sorted(os.listdir(projects)):
                self.move(projects / s, self.new / "projects" / self.remap_slug(s, False))
        names = sorted(os.listdir(self.old)) if self.old.is_dir() else []
        unknown = [n for n in names if n != "projects" and not self.native(n)]
        if unknown:
            raise Refusal(f"in {self.old}, appeared since the cutover and not classified "
                          f"native in {LAYOUT}: {', '.join(unknown)}; classify or move "
                          f"them, then rerun")
        for name in names:
            if name != "projects":
                self.move(self.old / name, self.new / name)


def dump_manifest(comment: str, entries) -> bytes:
    """The manifest's own layout: one key per line, lists inline."""
    blocks = []
    for e in entries:
        inner = ",\n".join(f"      {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
                           for k, v in e.items())
        blocks.append("    {\n" + inner + "\n    }")
    return ("{\n  \"_comment\": " + json.dumps(comment, ensure_ascii=False)
            + ",\n  \"entries\": [\n" + ",\n".join(blocks) + "\n  ]\n}\n").encode()


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="idh relocate harness", description=__doc__.splitlines()[0])
    ap.add_argument("--rollback", action="store_true", help="undo the cutover")
    ap.add_argument("--live", action="store_true",
                    help="act on this account's real HOME (the 0986 window only)")
    args = ap.parse_args(argv)
    home = Path(os.environ["HOME"])
    env = dict(os.environ)
    for why in (home_refusal(home, Path(pwd.getpwuid(os.getuid()).pw_dir), args.live),
                timer_refusal(env, home, args.live)):
        if why:
            print(f"idh: refusing: {why}", file=sys.stderr)
            return 1
    machine = Machine(home)
    try:
        return machine.rollback() if args.rollback else machine.cutover(env)
    except Refusal as exc:
        print(f"idh: refusing: {exc}", file=sys.stderr)
        return 1
