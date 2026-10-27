"""gaze_wall_time.endpoints: setup and closing read from tool calls, so headless seats count (ticket 1227)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gaze_wall_time as g  # noqa: E402


def _run(calls, launches=(), seats=(), end=200.0):
    return dict(start=0.0, end=end, calls=list(calls), launches=list(launches), seats=list(seats))


def test_headless_run_without_subagent_trace():
    r = _run(
        [
            (2, 1, "Bash", 'python3 "$IDH_ROOT/scripts/gaze_setup.py" 9'),
            (10, 0, "Bash", "git log"),
            (30, 1, "Bash", "python3 scripts/gaze_seat.py launch --runtime codex"),
            (90, 2, "Bash", "python3 scripts/seat_clock.py plan-check .panel/9"),
            (150, 3, "Bash", 'python3 "$IDH_ROOT/scripts/gaze_close.py" 9'),
        ]
    )
    e = g.endpoints(r)
    assert e["setup"] == 30 and e["setup_calls"] == 2
    assert e["closing"] == 200 - 92 and e["closing_calls"] == 1
    assert e["setup_script"] == 3 and e["close_script"] == 50


def test_dry_run_is_not_a_seat_and_missing_evidence_is_none():
    r = _run([(5, 1, "Bash", "python3 scripts/gaze_seat.py launch --dry-run")])
    e = g.endpoints(r)
    assert e["setup"] is None and e["closing"] is None
    assert e["setup_script"] is None and e["close_script"] is None


def test_agent_seats_use_their_traced_end():
    r = _run(
        [(20, 0, "Agent", "{}")],
        launches=[(20, "seat")],
        seats=[dict(end=120.0)],
    )
    e = g.endpoints(r)
    assert e["setup"] == 20 and e["closing"] == 80


def test_plan_check_before_any_seat_launch_is_not_closing():
    r = _run([(20, 2, "Bash", "python3 scripts/seat_clock.py plan-check .panel/9")])
    assert g.endpoints(r)["closing"] is None
