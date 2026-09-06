"""Tests for scripts/session_scratch.py — the orphan probe and its sweep.

The probe answers one question: which session scratch directories under the
user's temp root have no live process behind them (ticket 0854). Getting that
answer wrong in the safe direction costs disk; getting it wrong in the other
direction deletes a running session's scratchpad, so the liveness test is what
these tests are really about.

Two tiers:

* fast — the path and threshold logic, driven against a *fake* `/proc` tree, so
  no test depends on what happens to be running on the machine;
* integration — the real `/proc`, with a real live subprocess and a real exited
  one, which is the only way to show the signals the fake tier models actually
  exist. Every fixture lives under `tmp_path`; the machine's own temp root is
  read in exactly one test, which asserts nothing about its contents.
"""

import importlib.util
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
spec = importlib.util.spec_from_file_location(
    "session_scratch", SCRIPTS / "session_scratch.py"
)
ss = importlib.util.module_from_spec(spec)
sys.modules["session_scratch"] = ss
spec.loader.exec_module(ss)

OLD = 2 * 3600  # older than the min-age rail, so only liveness keeps a dir alive


def _plant(root: Path, key: str, session_id: str, payload_bytes: int = 0) -> Path:
    session_dir = root / key / session_id
    (session_dir / "scratchpad").mkdir(parents=True)
    (session_dir / "tasks").mkdir()
    if payload_bytes:
        (session_dir / "scratchpad" / "blob").write_bytes(b"\0" * payload_bytes)
    return session_dir


def _age(path: Path, seconds: int) -> None:
    """Push a session directory and its children into the past."""
    stamp = time.time() - seconds
    for entry in list(path.rglob("*")) + [path]:
        os.utime(entry, (stamp, stamp))


def _empty_proc(tmp_path: Path) -> str:
    """A `/proc` with no processes in it — every session reads as dead."""
    proc = tmp_path / "fakeproc-empty"
    proc.mkdir(exist_ok=True)
    return str(proc)


# ── liveness, against a fake /proc ────────────────────────────────────────────


def test_open_descriptor_inside_a_session_dir_means_live(tmp_path):
    """The signal that covers an idle session: the CLI holds its tasks/ fd."""
    root = tmp_path / "root"
    live_id, dead_id = str(uuid.uuid4()), str(uuid.uuid4())
    live_dir = _plant(root, "-key", live_id)
    _plant(root, "-key", dead_id)
    proc = tmp_path / "fakeproc"
    (proc / "4242" / "fd").mkdir(parents=True)
    (proc / "4242" / "fd" / "7").symlink_to(live_dir / "tasks")
    (proc / "4242" / "cmdline").write_bytes(b"claude\0")
    (proc / "4242" / "environ").write_bytes(b"PATH=/usr/bin\0")

    live = ss.live_session_ids(root, proc_root=str(proc))

    assert live == {live_id}


def test_session_id_in_the_environment_means_live(tmp_path):
    """A session with no open handle is still named by its own processes."""
    root = tmp_path / "root"
    live_id = str(uuid.uuid4())
    _plant(root, "-key", live_id)
    proc = tmp_path / "fakeproc"
    (proc / "77").mkdir(parents=True)
    (proc / "77" / "environ").write_bytes(
        f"HOME=/home/x\0CLAUDE_CODE_SESSION_ID={live_id}\0".encode()
    )
    (proc / "77" / "cmdline").write_bytes(b"bash\0")

    assert ss.live_session_ids(root, proc_root=str(proc)) == {live_id}


def test_unreadable_process_entries_are_skipped_not_fatal(tmp_path):
    """Another user's /proc entry raises on every read; that is not an error."""
    root = tmp_path / "root"
    _plant(root, "-key", str(uuid.uuid4()))
    proc = tmp_path / "fakeproc"
    (proc / "13").mkdir(parents=True)  # no environ, no cmdline, no fd
    (proc / "not-a-pid").mkdir()

    assert ss.live_session_ids(root, proc_root=str(proc)) == set()


# ── scan ─────────────────────────────────────────────────────────────────────


def test_scan_lists_the_dead_session_and_not_the_live_one(tmp_path):
    root = tmp_path / "root"
    live_id, dead_id = str(uuid.uuid4()), str(uuid.uuid4())
    live_dir = _plant(root, "-key-a", live_id)
    dead_dir = _plant(root, "-key-b", dead_id, payload_bytes=4096)
    _age(live_dir, OLD)
    _age(dead_dir, OLD)
    proc = tmp_path / "fakeproc"
    (proc / "4242" / "fd").mkdir(parents=True)
    (proc / "4242" / "fd" / "3").symlink_to(live_dir / "tasks")

    state = ss.scan(root=root, proc_root=str(proc), min_age_minutes=15)

    assert state["sessions_total"] == 2
    assert state["live"] == 1
    assert [o["session_id"] for o in state["orphans"]] == [dead_id]
    assert state["orphan_bytes"] >= 4096


def test_a_freshly_created_directory_is_never_an_orphan(tmp_path):
    """The age rail: a session that has not opened anything yet must survive."""
    root = tmp_path / "root"
    fresh_id = str(uuid.uuid4())
    _plant(root, "-key", fresh_id)  # mtime is now

    state = ss.scan(root=root, proc_root=_empty_proc(tmp_path), min_age_minutes=15)

    assert state["orphans"] == []
    assert state["live"] == 1


def test_non_session_directories_are_ignored(tmp_path):
    """Only `<cwd-key>/<uuid>` is ours; anything else is left alone."""
    root = tmp_path / "root"
    (root / "-key" / "not-a-session").mkdir(parents=True)
    (root / "-key" / "cache.db").write_text("x")
    _age(root / "-key", OLD)

    state = ss.scan(root=root, proc_root=_empty_proc(tmp_path))

    assert state["sessions_total"] == 0
    assert state["orphans"] == []


def test_missing_root_is_reported_not_raised(tmp_path):
    state = ss.scan(root=tmp_path / "absent", proc_root=_empty_proc(tmp_path))

    assert state["exists"] is False
    assert state["status"] == "ok"
    assert state["orphans"] == []


def test_many_orphans_raise_a_warning(tmp_path):
    root = tmp_path / "root"
    for _ in range(ss.WARN_ORPHAN_COUNT):
        _age(_plant(root, "-key", str(uuid.uuid4())), OLD)

    state = ss.scan(root=root, proc_root=_empty_proc(tmp_path))

    assert state["status"] == "warn"
    assert "orphan session directories" in " ".join(state["reasons"])


def test_a_handful_of_small_orphans_stays_ok(tmp_path):
    """Non-vacuity: the warning must not fire on every non-empty result."""
    root = tmp_path / "root"
    _age(_plant(root, "-key", str(uuid.uuid4())), OLD)

    state = ss.scan(root=root, proc_root=_empty_proc(tmp_path))

    assert state["orphan_count"] == 1
    assert state["status"] == "ok"


def test_symlinked_session_directory_is_not_followed(tmp_path):
    """A symlink reports is_dir() through its target; it is never a session."""
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "-key").mkdir(parents=True)
    (root / "-key" / str(uuid.uuid4())).symlink_to(outside)
    _age(root / "-key", OLD)

    state = ss.scan(root=root, proc_root=_empty_proc(tmp_path))

    assert state["orphans"] == []


# ── sweep ────────────────────────────────────────────────────────────────────


def test_sweep_removes_the_orphan_and_prunes_its_cwd_key(tmp_path):
    root = tmp_path / "root"
    live_id, dead_id = str(uuid.uuid4()), str(uuid.uuid4())
    live_dir = _plant(root, "-key-a", live_id)
    dead_dir = _plant(root, "-key-b", dead_id, payload_bytes=2048)
    _age(live_dir, OLD)
    _age(dead_dir, OLD)
    proc = tmp_path / "fakeproc"
    (proc / "9" / "fd").mkdir(parents=True)
    (proc / "9" / "fd" / "3").symlink_to(live_dir / "tasks")

    result = ss.sweep(root=root, proc_root=str(proc))

    assert [o["session_id"] for o in result["removed"]] == [dead_id]
    assert not dead_dir.exists()
    assert not (root / "-key-b").exists(), "emptied cwd-key dir not pruned"
    assert live_dir.exists(), "a live session's directory was removed"
    assert result["failed"] == []


def test_sweep_dry_run_removes_nothing(tmp_path):
    root = tmp_path / "root"
    dead_dir = _plant(root, "-key", str(uuid.uuid4()))
    _age(dead_dir, OLD)

    result = ss.sweep(root=root, proc_root=_empty_proc(tmp_path), dry_run=True)

    assert len(result["removed"]) == 1
    assert dead_dir.exists()


def test_sweep_reruns_the_liveness_test_itself(tmp_path, monkeypatch):
    """A session can start between the probe and the sweep: never trust a list."""
    calls = []
    real_scan = ss.scan

    def counting_scan(**kwargs):
        calls.append(kwargs)
        return real_scan(**kwargs)

    monkeypatch.setattr(ss, "scan", counting_scan)
    root = tmp_path / "root"
    _age(_plant(root, "-key", str(uuid.uuid4())), OLD)

    ss.sweep(root=root, proc_root=_empty_proc(tmp_path))

    assert len(calls) == 1, "sweep must compute liveness itself, not inherit it"


# ── root resolution ──────────────────────────────────────────────────────────


def test_scratch_root_prefers_the_explicit_override():
    assert ss.scratch_root({"CLAUDE_SESSION_SCRATCH_ROOT": "/x/y"}) == Path("/x/y")


def test_scratch_root_follows_the_runtime_temp_knob_over_tmpdir():
    root = ss.scratch_root({"CLAUDE_CODE_TMPDIR": "/fast", "TMPDIR": "/slow"})
    assert root == Path(f"/fast/claude-{os.getuid()}")


def test_scratch_root_falls_back_to_tmp():
    assert ss.scratch_root({}) == Path(f"/tmp/claude-{os.getuid()}")


# ── the real /proc ───────────────────────────────────────────────────────────


@pytest.mark.integration
def test_live_and_dead_pids_against_the_real_proc(tmp_path):
    """The discriminating case: one dir held by a live pid, one by a dead pid.

    Both directories are aged past the min-age rail, so nothing but the liveness
    test separates them. Three fixtures, one per signal the probe claims:

    * `fd` — a live process holding an open descriptor on the session's tasks/
      directory, told the path on stdin so neither its argv nor its environment
      names the session id (this isolates the fd signal);
    * `env` — a live process carrying the session id in its environment only;
    * `dead` — a process that carried the id and has since exited.
    """
    root = tmp_path / "root"
    fd_id, env_id, dead_id = (str(uuid.uuid4()) for _ in range(3))
    fd_dir = _plant(root, "-key-a", fd_id)
    env_dir = _plant(root, "-key-b", env_id)
    dead_dir = _plant(root, "-key-c", dead_id, payload_bytes=1024)
    for d in (fd_dir, env_dir, dead_dir):
        _age(d, OLD)

    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys,time; p=sys.stdin.readline().strip(); "
            "os.open(p, os.O_RDONLY); print('ready', flush=True); time.sleep(120)",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    namer = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        env={**os.environ, "CLAUDE_CODE_SESSION_ID": env_id},
    )
    # A process that really did exist and really is gone.
    exited = subprocess.run(
        [sys.executable, "-c", "pass"],
        env={**os.environ, "CLAUDE_CODE_SESSION_ID": dead_id},
        check=False,
    )
    assert exited.returncode == 0
    try:
        holder.stdin.write(f"{fd_dir / 'tasks'}\n")
        holder.stdin.flush()
        assert holder.stdout.readline().strip() == "ready"

        state = ss.scan(root=root, min_age_minutes=15)  # the machine's real /proc

        assert [o["session_id"] for o in state["orphans"]] == [dead_id], (
            "the probe must list exactly the dead session"
        )
        assert state["live"] == 2
    finally:
        for proc in (holder, namer):
            proc.kill()
            proc.wait(timeout=10)

    # Once the holders are gone, all three are orphans — the fixture proves the
    # liveness test was doing the work, not some property of the directories.
    after = ss.scan(root=root, min_age_minutes=15)
    assert sorted(o["session_id"] for o in after["orphans"]) == sorted(
        [fd_id, env_id, dead_id]
    )


@pytest.mark.integration
def test_cli_reports_the_machines_own_root_without_touching_it():
    """A read-only run against the real root must exit 0 and print valid JSON."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "session_scratch.py"), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr
    import json

    state = json.loads(result.stdout)
    assert state["root"].endswith(f"claude-{os.getuid()}")
    assert "orphans" in state and "status" in state


@pytest.mark.integration
def test_sweep_refuses_a_symlinked_root(tmp_path):
    """A symlinked root must not be operated on, by scan() or by --sweep.

    `sweep()`'s containment re-derivation cannot catch this: it resolves
    symlinks on BOTH sides, so a symlinked root always passes it. The refusal
    has to happen before anything is listed.
    """
    real = tmp_path / "victim-real"
    victim = _plant(real, "-key-a", str(uuid.uuid4()), payload_bytes=64)
    _age(victim, OLD)
    link = tmp_path / "symlinked-root"
    link.symlink_to(real, target_is_directory=True)

    state = ss.scan(root=link, proc_root=_empty_proc(tmp_path), min_age_minutes=0)
    assert state["orphans"] == [], "a symlinked root was scanned through"
    assert state["status"] == "warn"
    assert any("symlink" in r for r in state["reasons"])

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "session_scratch.py"),
            "--root",
            str(link),
            "--sweep",
            "--min-age-minutes",
            "0",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert victim.is_dir(), "--sweep deleted through a symlinked root"


@pytest.mark.integration
def test_scan_survives_an_unreadable_cwd_key_directory(tmp_path):
    """`scan()` documents "Never raises." — an unreadable dir must be skipped.

    The same unguarded `iterdir()` is racy against this ticket's own hook,
    which `rmdir`s an emptied cwd-key directory on every session exit.
    """
    if os.getuid() == 0:
        pytest.skip("root bypasses the mode bits, so the fixture cannot be built")
    root = tmp_path / "root"
    orphan_id = str(uuid.uuid4())
    orphan = _plant(root, "-key-readable", orphan_id, payload_bytes=64)
    _age(orphan, OLD)
    blocked = root / "-key-blocked"
    (blocked / str(uuid.uuid4())).mkdir(parents=True)
    blocked.chmod(0o000)
    try:
        state = ss.scan(root=root, proc_root=_empty_proc(tmp_path), min_age_minutes=0)

        assert [o["session_id"] for o in state["orphans"]] == [orphan_id], (
            "the readable orphan must still be found"
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "session_scratch.py"),
                "--root",
                str(root),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
    finally:
        blocked.chmod(0o700)


def test_a_truncated_walk_warns_that_the_totals_are_a_floor(tmp_path, monkeypatch):
    """Truncation must not read as an all-clear.

    With the ceiling hit, `root_bytes`/`orphan_bytes` are a floor. A `status`
    of `ok` there is the "all-clear indistinguishable from could-not-look"
    shape `rules/coding-bash.md` names.
    """
    root = tmp_path / "root"
    _age(_plant(root, "-key", str(uuid.uuid4()), payload_bytes=64), OLD)
    monkeypatch.setattr(ss, "MAX_ENTRIES", 1)

    state = ss.scan(root=root, proc_root=_empty_proc(tmp_path), min_age_minutes=0)

    assert state["truncated"] is True
    assert state["status"] == "warn"
    assert any("truncated" in r or "floor" in r for r in state["reasons"])


# ── documentation coupling ───────────────────────────────────────────────────


def test_healthcheck_documents_the_temp_check():
    """Item 12 exists and reads the probe field, not an ad-hoc command."""
    text = (REPO_ROOT / "skills" / "healthcheck" / "SKILL.md").read_text()
    assert "12. **Session scratch" in text
    assert "session_scratch" in text


def test_molt_wires_the_sweep():
    text = (REPO_ROOT / "skills" / "molt" / "SKILL.md").read_text()
    assert "session_scratch.py --sweep" in text
