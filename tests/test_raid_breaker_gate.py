"""The raid breaker must separate a long live gate from a silent executor."""

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("raid_gate_state", SCRIPTS / "raid_gate_state.py")
assert spec and spec.loader
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)


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
        cwd=own, stdout=subprocess.DEVNULL,
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
