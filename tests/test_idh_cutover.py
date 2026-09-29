"""`idh relocate harness` and its rollback on a disposable HOME (ticket 0985).

Every run builds a fixture HOME whose ~/.claude is a clone of the tracked
harness plus native runtime files, two linked worktrees (one inside the
checkout, one outside), a ~/.claude.json with path-keyed projects, and a
`systemctl` stub that keeps timer state in the fixture. XDG_RUNTIME_DIR points
inside the fixture HOME, so even a real systemctl could not reach the
developer's user manager. Nothing here reads or writes the developer's HOME.
"""

import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from tracked_tree import tracked_checkout

pytestmark = pytest.mark.integration

REPO = tracked_checkout()
GIT = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
TIMERS_ON = ("claude-refresh.timer", "claude-telemetry-prune.timer")


def slug(path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def git(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return subprocess.run([*GIT, *args], cwd=cwd, env=env, capture_output=True,
                          text=True, check=True).stdout


@pytest.fixture(scope="module")
def seed(tmp_path_factory):
    """A git repository holding the tracked harness minus the bulky trees."""
    dest = tmp_path_factory.mktemp("seed") / "repo"
    skip = {"tests", "docs", "projects", "tickets"}
    shutil.copytree(REPO, dest, symlinks=True,
                    ignore=lambda d, names: [n for n in names if Path(d) == REPO and n in skip])
    (dest / "tickets").mkdir()
    shutil.copy2(REPO / "tickets" / "AGENTS.md", dest / "tickets" / "AGENTS.md")
    git("init", "-q", str(dest))
    git("add", "-A", cwd=dest)
    git("commit", "-qm", "seed", cwd=dest)
    return dest


class Machine:
    def __init__(self, root: Path, seed: Path):
        self.root, self.home = root, root / "home"
        self.old, self.new = self.home / ".claude", self.home / ".idh"
        self.home.mkdir(parents=True)
        git("clone", "-q", str(seed), str(self.old))
        self._stub()
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{self.root / 'bin'}:/usr/bin:/bin",
            "XDG_RUNTIME_DIR": str(self.home / "run"),
            "GIT_CONFIG_GLOBAL": os.devnull,
        }
        (self.home / "run").mkdir()
        self._populate()
        self.new.symlink_to(self.old)
        r = self.idh("install")
        assert r.returncode == 0, r.stdout + r.stderr

    def _stub(self):
        (self.root / "bin").mkdir()
        state = self.root / "timers"
        state.mkdir()
        for timer in TIMERS_ON:
            (state / timer).touch()
        self.log = self.root / "systemctl.log"
        stub = self.root / "bin" / "systemctl"
        stub.write_text(f"""#!/bin/sh
echo "$*" >> "{self.log}"
[ "$1" = --user ] && shift
case "$1" in
  is-active) [ -e "{state}/$2" ] && {{ echo active; exit 0; }}; echo inactive; exit 3 ;;
  stop) rm -f "{state}/$2" ;;
  start) touch "{state}/$2" ;;
  enable) [ "$2" = --now ] && touch "{state}/$3" ;;
esac
exit 0
""")
        stub.chmod(0o755)
        self.timer_state = state

    def _populate(self):
        old, home = self.old, self.home
        mem = old / "projects" / slug(old) / "memory"
        mem.mkdir(parents=True)
        (mem / "MEMORY.md").write_text("- harness memory\n")
        other = old / "projects" / "-srv-other" / "memory"
        other.mkdir(parents=True)
        (other / "MEMORY.md").write_text("- other memory\n")
        git("add", "-A", cwd=old)
        git("commit", "-qm", "memory", cwd=old)
        # Native runtime state, never tracked.
        (old / ".credentials.json").write_text('{"fixture": true}\n')
        (old / ".credentials.json").chmod(0o600)
        (old / "settings.json").write_text("{}\n")
        (old / "history.jsonl").write_text('{"h": 1}\n')
        (old / "sessions").mkdir()
        (old / "sessions" / "1.json").write_text("{}\n")
        (old / "projects" / slug(old) / "t1.jsonl").write_text("transcript\n")
        (old / "projects" / slug(old) / "sub").mkdir()
        (old / "projects" / slug(old) / "sub" / "a.json").write_text("{}\n")
        (old / "projects" / "-srv-other" / "t2.jsonl").write_text("transcript\n")
        (old / "projects" / "-native-only").mkdir()
        (old / "projects" / "-native-only" / "t3.jsonl").write_text("transcript\n")
        (old / ".env").write_text("K=v\n")
        private = home / ".config" / "harness" / "private" / "skills" / "email"
        private.mkdir(parents=True)
        (private / "SKILL.md").write_text("---\nname: email\n---\n")
        (old / "skills" / "email").symlink_to(private)
        # Worktrees: one inside the checkout, one outside it.
        self.wt_in = old / ".claude" / "worktrees" / "wt1"
        self.wt_out = self.root / "elsewhere" / "wt2"
        git("worktree", "add", "-q", "-b", "wt1", str(self.wt_in), cwd=old)
        git("worktree", "add", "-q", "-b", "wt2", str(self.wt_out), cwd=old)
        (self.wt_in / "CLAUDE.md").write_text("work in progress\n")  # uncommitted
        claude_json = home / ".claude.json"
        claude_json.write_text(json.dumps({"projects": {
            str(old): {"trust": True},
            str(self.wt_in): {"trust": True},
            "/srv/other": {"trust": True},
        }, "numStartups": 3}, indent=2) + "\n")
        claude_json.chmod(0o600)

    def idh(self, *args, extra=None):
        """bin/idh wherever the checkout is: after a crash between dropping the
        ~/.idh pointer and the move, only ~/.claude/bin/idh exists (the live
        checklist names the same fallback)."""
        env = {**self.env, **(extra or {})}
        idh = self.new / "bin" / "idh"
        if not idh.exists():
            idh = self.old / "bin" / "idh"
        return subprocess.run([sys.executable, str(idh), *args],
                              env=env, capture_output=True, text=True, timeout=120)

    def validate(self, *args):
        return subprocess.run(
            [sys.executable, str(self.new / "scripts" / "validate-projections.py"), *args],
            env=self.env, capture_output=True, text=True, timeout=60)

    def snapshot(self) -> dict:
        """Bytes, modes and link targets of the fixture HOME and the outside
        worktree, except git's stat cache, bytecode and the cutover's journal
        (~/.local/state/idh, kept on purpose as the record of the run)."""
        out = {}
        for top, dirs, files in (w for d in ("home", "elsewhere") for w in os.walk(self.root / d)):
            for name in dirs + files:
                p = Path(top) / name
                rel = p.relative_to(self.root).as_posix()
                if rel.endswith("/.git/index") or "__pycache__" in rel \
                        or rel.startswith("home/.local/state"):
                    continue
                st = p.lstat()
                if stat.S_ISLNK(st.st_mode):
                    out[rel] = ("link", os.readlink(p))
                elif stat.S_ISDIR(st.st_mode):
                    out[rel] = ("dir", stat.S_IMODE(st.st_mode))
                else:
                    out[rel] = ("file", stat.S_IMODE(st.st_mode),
                                hashlib.sha256(p.read_bytes()).hexdigest())
            dirs[:] = [d for d in dirs if not (Path(top) / d).is_symlink()]
        return out

    def active_timers(self):
        return sorted(p.name for p in self.timer_state.iterdir())


@pytest.fixture
def machine(tmp_path, seed):
    return Machine(tmp_path, seed)


def diff(a: dict, b: dict) -> list:
    """(path, before, after) for every path whose bytes, mode or link differ."""
    return sorted((k, a.get(k), b.get(k)) for k in a.keys() | b.keys() if a.get(k) != b.get(k))


def assert_same(before: dict, after: dict, label="") -> None:
    d = diff(before, after)
    assert not d, f"{label}\n" + "\n".join(map(str, d))


def test_cutover_then_rollback_round_trip(machine):
    m = machine
    pre = m.snapshot()
    r = m.idh("relocate", "harness")
    assert r.returncode == 0, r.stdout + r.stderr

    # The checkout moved; the native root is a real directory of native files
    # and per-entry links.
    assert (m.new / ".git").is_dir() and not m.new.is_symlink()
    assert m.old.is_dir() and not m.old.is_symlink() and not (m.old / ".git").exists()
    for name in ("CLAUDE.md", "RTK.md", "rules", "skills", "tickets"):
        assert (m.old / name).is_symlink(), name
        assert (m.old / name).resolve() == (m.new / name).resolve()
    assert not (m.old / "scripts").exists()
    assert (m.old / ".credentials.json").read_text() == '{"fixture": true}\n'
    assert (m.new / ".env").is_file() and not (m.old / ".env").exists()
    # Project store: the harness slug is renamed to the new key, memory stays
    # tracked in the checkout and is linked back; transcripts are native.
    new_slug = slug(m.new)
    assert not (m.new / "projects" / slug(m.old)).exists()
    assert (m.new / "projects" / new_slug / "memory" / "MEMORY.md").is_file()
    link = m.old / "projects" / new_slug / "memory"
    assert link.is_symlink() and link.resolve() == (m.new / "projects" / new_slug / "memory")
    assert (m.old / "projects" / new_slug / "t1.jsonl").is_file()
    assert (m.old / "projects" / new_slug / "sub" / "a.json").is_file()
    assert (m.old / "projects" / "-srv-other" / "memory").is_symlink()
    assert (m.old / "projects" / "-native-only" / "t3.jsonl").is_file()
    assert not (m.new / "projects" / "-native-only").exists()

    # The 0983 validator passes on the rewritten manifest ...
    for runtime in ("claude", "codex", "pi"):
        v = m.validate(runtime)
        assert v.returncode == 0, v.stderr
    # ... and the unrewritten one refuses, naming the native root.
    pre_manifest = m.root / "pre-projections.json"
    pre_manifest.write_bytes(git("show", "HEAD:adapters/projections.json", cwd=m.new).encode())
    v = m.validate("claude", "--manifest", str(pre_manifest))
    assert v.returncode == 1
    assert f"FOREIGN: {m.old} is a real directory" in v.stderr

    # Worktrees survive: both find their repository, the WIP is intact.
    wt_in_new = m.new / ".claude" / "worktrees" / "wt1"
    assert "CLAUDE.md" in git("status", "--porcelain", cwd=wt_in_new)
    assert git("rev-parse", "--abbrev-ref", "HEAD", cwd=m.wt_out).strip() == "wt2"
    assert "prunable" not in git("worktree", "list", cwd=m.new)

    # ~/.claude.json re-keyed for the checkout only.
    keys = set(json.loads((m.home / ".claude.json").read_text())["projects"])
    assert keys == {str(m.new), str(wt_in_new), "/srv/other"}

    # Timers paused around the move, then resumed.
    log = m.log.read_text()
    for timer in TIMERS_ON:
        assert f"--user stop {timer}" in log and f"--user start {timer}" in log
        assert log.index(f"--user stop {timer}") < log.index(f"--user start {timer}")
    assert set(TIMERS_ON) <= set(m.active_timers())

    # Idempotent: a second cutover changes nothing.
    post = m.snapshot()
    r = m.idh("relocate", "harness")
    assert r.returncode == 0, r.stdout + r.stderr
    assert_same(post, m.snapshot())

    r = m.idh("relocate", "harness", "--rollback")
    assert r.returncode == 0, r.stdout + r.stderr
    assert_same(pre, m.snapshot())
    assert set(TIMERS_ON) <= set(m.active_timers())
    assert "CLAUDE.md" in git("status", "--porcelain", cwd=m.wt_in)
    assert "prunable" not in git("worktree", "list", cwd=m.old)
    r = m.idh("relocate", "harness", "--rollback")
    assert r.returncode == 0, r.stdout + r.stderr
    assert_same(pre, m.snapshot())


def test_refuses_a_dirty_tree_and_a_foreign_file(machine):
    m = machine
    timers = m.active_timers()
    (m.old / "CLAUDE.md").write_text("edited\n")
    pre = m.snapshot()
    r = m.idh("relocate", "harness")
    assert r.returncode != 0
    assert "CLAUDE.md" in r.stderr
    assert_same(pre, m.snapshot())
    git("checkout", "--", "CLAUDE.md", cwd=m.old)

    (m.old / "mystery.bin").write_text("whose?\n")
    pre = m.snapshot()
    r = m.idh("relocate", "harness")
    assert r.returncode != 0
    assert "mystery.bin" in r.stderr
    assert_same(pre, m.snapshot())
    assert m.active_timers() == timers, "a refusal paused a timer"


def test_refuses_timer_calls_that_could_reach_another_user_manager(machine):
    m = machine
    pre = m.snapshot()
    r = m.idh("relocate", "harness", extra={"XDG_RUNTIME_DIR": "/run/user/0"})
    assert r.returncode != 0
    assert "XDG_RUNTIME_DIR" in r.stderr
    assert_same(pre, m.snapshot())
    assert "stop" not in m.log.read_text()


def _cutover_module():
    spec = importlib.util.spec_from_file_location("cutover", REPO / "adapters" / "cutover.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_real_home_is_refused_without_the_live_flag():
    cutover = _cutover_module()
    real = Path("/home/someone")
    assert cutover.home_refusal(real, real, live=False)
    assert cutover.home_refusal(real / ".", real, live=False)
    assert cutover.home_refusal(real, real, live=True) is None
    assert cutover.home_refusal(Path("/tmp/x/home"), real, live=False) is None
    assert cutover.home_refusal(Path("/tmp/x/home"), real, live=True)


def test_every_cutover_crash_point_rolls_back_and_resumes(tmp_path, seed):
    k, count = 0, None
    while count is None:
        k += 1
        m = Machine(tmp_path / f"rb{k}", seed)
        pre = m.snapshot()
        r = m.idh("relocate", "harness", extra={"IDH_CUTOVER_CRASH_AT": str(k)})
        if r.returncode == 0:
            count = k - 1
            break
        assert r.returncode == 99, (k, r.stdout + r.stderr)
        # A crash then a rollback restores the pre-state exactly.
        r = m.idh("relocate", "harness", "--rollback")
        assert r.returncode == 0, (k, r.stdout + r.stderr)
        assert_same(pre, m.snapshot(), k)
        # A crash then a rerun completes the cutover.
        m2 = Machine(tmp_path / f"re{k}", seed)
        r = m2.idh("relocate", "harness", extra={"IDH_CUTOVER_CRASH_AT": str(k)})
        assert r.returncode == 99
        r = m2.idh("relocate", "harness")
        assert r.returncode == 0, (k, r.stdout + r.stderr)
        assert m2.validate("claude").returncode == 0, k
        shutil.rmtree(tmp_path / f"re{k}", ignore_errors=True)
        shutil.rmtree(tmp_path / f"rb{k}", ignore_errors=True)
    assert count >= 10, f"only {count} mutation checkpoints: the crash hook is not wired"


def test_every_rollback_crash_point_resumes(tmp_path, seed):
    k = 0
    while True:
        k += 1
        m = Machine(tmp_path / f"m{k}", seed)
        pre = m.snapshot()
        assert m.idh("relocate", "harness").returncode == 0
        r = m.idh("relocate", "harness", "--rollback", extra={"IDH_CUTOVER_CRASH_AT": str(k)})
        if r.returncode == 0:
            break
        assert r.returncode == 99, (k, r.stdout + r.stderr)
        r = m.idh("relocate", "harness")
        # Refused, or (crash before the rollback marked its journal) a no-op.
        assert r.returncode != 0 or "already cut over" in r.stdout, (k, r.stdout)
        r = m.idh("relocate", "harness", "--rollback")
        assert r.returncode == 0, (k, r.stdout + r.stderr)
        assert_same(pre, m.snapshot(), k)
        shutil.rmtree(tmp_path / f"m{k}", ignore_errors=True)
    assert k > 10
