"""The raid breaker must separate a long live gate from a silent executor."""

import argparse
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import pytest

from child_env import child_env


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("raid_gate_state", SCRIPTS / "raid_gate_state.py")
assert spec and spec.loader
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)
sys.path.insert(0, str(SCRIPTS))
bspec = importlib.util.spec_from_file_location("raid_breaker", SCRIPTS / "raid-breaker.py")
assert bspec and bspec.loader
breaker = importlib.util.module_from_spec(bspec)
bspec.loader.exec_module(breaker)


class Sim:
    """Injected clock; sleep advances it, snapshot and gate are scripted."""

    def __init__(self, snaps=None, gates=None):
        self.t = 1_000_000.0
        self.snaps = snaps or (lambda t: "same")
        self.gates = gates or (lambda t: None)

    def run(self, deadline, tmp_path, monkeypatch, gate_max=1800):
        args = argparse.Namespace(
            worktree=tmp_path, deadline=deadline, poll_seconds=10,
            stall_seconds=600, gate_max_seconds=gate_max)
        monkeypatch.setattr(breaker, "read_marker", lambda _p: self.gates(self.t))
        code = breaker.run(args, clock=lambda: self.t,
                           sleep=lambda s: setattr(self, "t", self.t + s),
                           take=lambda _w: self.snaps(self.t))
        return code, self.t - 1_000_000.0


def test_wait_wakes_once_on_staged_stall(tmp_path, monkeypatch) -> None:
    code, elapsed = Sim().run(3600, tmp_path, monkeypatch)
    assert code == 1
    assert 600 < elapsed <= 620


def test_wait_long_silence_with_fresh_heartbeat_is_quiet(tmp_path, monkeypatch) -> None:
    sim = Sim(gates=lambda t: (1_000_000.0, t - 1))
    assert sim.run(1500, tmp_path, monkeypatch)[0] == 0


def test_wait_gate_past_max_wakes(tmp_path, monkeypatch) -> None:
    sim = Sim(gates=lambda t: (1_000_000.0, t - 1))
    code, elapsed = sim.run(3600, tmp_path, monkeypatch, gate_max=900)
    assert code == 1
    assert 900 < elapsed <= 920


def test_wait_progress_resets_window(tmp_path, monkeypatch) -> None:
    sim = Sim(snaps=lambda t: int((t - 1_000_000.0) // 500))
    assert sim.run(3000, tmp_path, monkeypatch)[0] == 0


def test_wait_gate_exit_restarts_window(tmp_path, monkeypatch) -> None:
    sim = Sim(gates=lambda t: (1_000_000.0, t - 1) if t - 1_000_000.0 < 1000 else None)
    code, elapsed = sim.run(3000, tmp_path, monkeypatch)
    assert code == 1
    assert 1600 < elapsed <= 1630


def test_wait_deadline_is_quiet(tmp_path, monkeypatch) -> None:
    assert Sim().run(300, tmp_path, monkeypatch)[0] == 0


@pytest.mark.integration
def test_wait_cli_on_real_repo(tmp_path: Path) -> None:
    env = child_env()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
    base = [sys.executable, str(SCRIPTS / "raid-breaker.py"), "--worktree", str(tmp_path),
            "--gate-max-seconds", "900", "--wait"]
    done = subprocess.run(base + ["--deadline", "1", "--poll-seconds", "0.2"],
                          env=env, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0
    bad = subprocess.run(base, env=env, capture_output=True, text=True, timeout=30)
    assert bad.returncode == 2


def test_long_gate_without_edits_and_bounded_timeout() -> None:
    now = 1000.0
    assert state.classify(now, 0, (now - 700, now - 1), 600, 1800) == "GATE_RUNNING"
    assert state.classify(now, 0, None, 600, 1800) == "STALL"
    assert state.classify(now, 0, (now - 1900, now - 1), 600, 1800) == "GATE_TIMEOUT"
    assert state.classify(now, 0, (now - 700, now - 60), 600, 1800) == "STALL"
    assert state.classify(now, now - 10, None, 600, 1800) == "ACTIVE"


@pytest.mark.integration
def test_gate_heartbeat_is_tied_to_its_worktree(tmp_path: Path) -> None:
    own = tmp_path / "own"
    other = tmp_path / "other"
    own.mkdir()
    other.mkdir()
    (own / "Makefile").write_text("check:\n\t@sleep 1\n")
    process = subprocess.Popen(
        [sys.executable, str(SCRIPTS / "raid-gate.py"), "--", "make", "check"],
        cwd=own, stdout=subprocess.DEVNULL, env=child_env(),
    )
    try:
        for _ in range(40):
            gate = state.read_marker(state.marker_path(own))
            if gate:
                break
            time.sleep(0.025)
        assert gate is not None
        assert state.read_marker(state.marker_path(other)) is None
        assert state.classify(time.time(), 0, gate, 600, 1800) == "GATE_RUNNING"
        assert process.wait(timeout=5) == 0
        assert state.read_marker(state.marker_path(own)) is None
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


def test_evaluate_is_pure_step() -> None:
    status, st = state.evaluate(100.0, None, "a", None, 600, 1800)
    assert status == "ACTIVE"
    status, st = state.evaluate(701.0, st, "a", None, 600, 1800)
    assert status == "STALL"
    status, _ = state.evaluate(702.0, st, "b", None, 600, 1800)
    assert status == "ACTIVE"


@pytest.mark.integration
def test_snapshot_sees_second_edit_and_survives_git_failure(tmp_path: Path) -> None:
    env = child_env()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
    (tmp_path / "f").write_text("a\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "f"], check=True, env=env)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qm", "x"], check=True, env=env)
    (tmp_path / "f").write_text("b\n")
    first = breaker.snapshot(tmp_path)
    (tmp_path / "f").write_text("c\n")
    assert breaker.snapshot(tmp_path) != first
    assert breaker.snapshot(tmp_path / "missing") is None


def test_wait_git_failure_keeps_stall_window(tmp_path, monkeypatch) -> None:
    sim = Sim(snaps=lambda t: "same" if (t // 10) % 2 else None)
    code, elapsed = sim.run(3600, tmp_path, monkeypatch)
    assert code == 1
    assert 600 < elapsed <= 620


@pytest.mark.integration
def test_snapshot_survives_non_utf8_and_sees_untracked_rewrite(tmp_path: Path) -> None:
    env = child_env()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
    (tmp_path / "f").write_text("a\n")
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "add", "f"], check=True, env=env)
    subprocess.run([*git, "commit", "-qm", "x"], check=True, env=env)
    (tmp_path / "f").write_bytes(b"caf\xe9\n")
    assert breaker.snapshot(tmp_path) is not None
    (tmp_path / "new").write_text("1\n")
    first = breaker.snapshot(tmp_path)
    (tmp_path / "new").write_text("22\n")
    assert breaker.snapshot(tmp_path) != first
