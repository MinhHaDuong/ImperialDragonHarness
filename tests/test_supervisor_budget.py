"""Tests for the supervisor budget convergence rule.

These thresholds lived as prose in nightbeat-supervisor/SKILL.md, where
nothing checked that an executor applied them. Each test below is a case the
prose stated but could not enforce.
"""

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "supervisor-budget.py"

_spec = importlib.util.spec_from_file_location("supervisor_budget", SCRIPT)
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def _repair(project="p", phase="raid", days_ago=1):
    return {
        "action": "repair",
        "project": project,
        "phase": phase,
        "ts": (NOW - timedelta(days=days_ago)).isoformat(),
    }


def _decide(current=1.0, default=1.0, journal=None):
    return sb.decide(
        current=current,
        default=default,
        project="p",
        phase="raid",
        journal=journal or [],
        now=NOW,
    )


def test_raises_by_twenty_percent():
    d = _decide(current=1.0, default=1.0)
    assert d["action"] == "raise"
    assert d["value"] == 1.2


def test_never_exceeds_twice_the_module_default():
    d = _decide(current=1.9, default=1.0)
    assert d["action"] == "raise"
    assert d["value"] == 2.0, "raise must clamp to 2x the default"


def test_at_the_ceiling_files_a_ticket_instead_of_raising():
    d = _decide(current=2.0, default=1.0)
    assert d["action"] == "ticket"
    assert "ceiling" in d["reason"]


def test_warns_above_one_and_a_half_but_still_raises():
    d = _decide(current=1.3, default=1.0)
    assert d["action"] == "raise"
    assert d["warn"] is True, "a raise past 1.5x default must be flagged"


def test_no_warning_below_the_threshold():
    d = _decide(current=1.0, default=1.0)
    assert d["warn"] is False


def test_three_repairs_in_the_window_stops_raising():
    d = _decide(current=1.0, default=1.0, journal=[_repair() for _ in range(3)])
    assert d["action"] == "ticket"
    assert "not converging" in d["reason"]


def test_two_repairs_still_raises():
    d = _decide(current=1.0, default=1.0, journal=[_repair() for _ in range(2)])
    assert d["action"] == "raise"


def test_repairs_outside_the_window_do_not_count():
    old = [_repair(days_ago=30) for _ in range(5)]
    assert _decide(current=1.0, default=1.0, journal=old)["action"] == "raise"


def test_repairs_for_another_phase_do_not_count():
    other = [_repair(phase="pick_ticket") for _ in range(5)]
    assert _decide(current=1.0, default=1.0, journal=other)["action"] == "raise"


def test_repairs_for_another_project_do_not_count():
    other = [_repair(project="q") for _ in range(5)]
    assert _decide(current=1.0, default=1.0, journal=other)["action"] == "raise"


def test_non_repair_entries_do_not_count():
    idle = [{"action": "idle", "project": "p", "phase": "raid",
             "ts": NOW.isoformat()} for _ in range(5)]
    assert _decide(current=1.0, default=1.0, journal=idle)["action"] == "raise"


def test_malformed_journal_lines_are_survivable():
    journal = [{"action": "repair", "project": "p", "phase": "raid"}]  # no ts
    assert _decide(current=1.0, default=1.0, journal=journal)["action"] == "raise"
