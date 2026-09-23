"""A live PR continues; a merged or closed PR stops at the next boundary."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-pr-open.py"
SKILLS = SCRIPT.parents[1] / "skills"


def _gh_stub(tmp_path):
    binary = tmp_path / "gh"
    binary.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$GH_CALLS"\n'
        'if [ -n "$GH_DELAY_SECONDS" ]; then exec sleep "$GH_DELAY_SECONDS"; fi\n'
        'cat "$GH_STATE"\n'
    )
    binary.chmod(0o755)
    state = tmp_path / "state"
    calls = tmp_path / "calls"
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}", GH_STATE=str(state), GH_CALLS=str(calls))
    return state, calls, env


def _phase(env, phase):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "826", phase],
        env=env,
        capture_output=True,
        text=True,
    )


def test_merged_pr_stops_at_next_transition(tmp_path):
    state, calls, env = _gh_stub(tmp_path)
    state.write_text("OPEN\n")
    assert _phase(env, "review-panel").returncode == 0
    state.write_text("MERGED\n")
    result = _phase(env, "external-request")
    assert result.returncode == 3
    assert "/gaze stopped: phase=external-request state=MERGED pr=826" in result.stderr
    assert len(calls.read_text().splitlines()) == 2


def test_open_pr_passes_every_transition(tmp_path):
    state, calls, env = _gh_stub(tmp_path)
    state.write_text("OPEN\n")
    phases = ["setup", "review-panel", "external-request", "simplify", "external-harvest", "gate", "verdict", "reroll-fix"]
    for phase in phases:
        result = _phase(env, phase)
        assert result.returncode == 0
        assert not result.stderr
    assert len(calls.read_text().splitlines()) == len(phases)


def test_closed_and_unknown_states_stop(tmp_path):
    state, _, env = _gh_stub(tmp_path)
    for value, expected in [("CLOSED", "CLOSED"), ("", "UNKNOWN")]:
        state.write_text(value)
        result = _phase(env, "verdict")
        assert result.returncode == 3
        assert f"phase=verdict state={expected}" in result.stderr


@pytest.mark.integration
def test_merged_verdict_guard_prevents_following_post(tmp_path):
    state, _, env = _gh_stub(tmp_path)
    state.write_text("MERGED\n")
    posted = tmp_path / "posted"
    result = subprocess.run(
        f'python3 "{SCRIPT}" 826 verdict && touch "{posted}"',
        shell=True,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert not posted.exists()


@pytest.mark.integration
def test_stalled_gh_state_lookup_stops_with_unknown(tmp_path):
    state, _, env = _gh_stub(tmp_path)
    state.write_text("OPEN\n")
    env["GH_DELAY_SECONDS"] = "2"
    continued = tmp_path / "continued"
    started = time.monotonic()
    result = subprocess.run(
        f'python3 "{SCRIPT}" 826 review-panel --timeout-seconds 0.1 && touch "{continued}"',
        shell=True,
        env=env,
        capture_output=True,
        text=True,
    )
    assert time.monotonic() - started < 1
    assert result.returncode == 3
    assert not continued.exists()
    assert "phase=review-panel state=UNKNOWN" in result.stderr
    assert "timed out" in result.stderr


def test_gaze_guards_costly_transitions_and_verdict():
    gaze = (SKILLS / "gaze" / "SKILL.md").read_text()
    gate = (SKILLS / "verify-gate" / "SKILL.md").read_text()
    for phase in ("setup", "review-panel", "external-request", "simplify", "external-harvest", "gate", "verdict", "reroll-fix"):
        assert f'check-pr-open.py" <pr-number> {phase}' in gaze
    assert 'check-pr-open.py" <pr-number> verdict' in gate
