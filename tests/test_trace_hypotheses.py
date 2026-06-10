"""Tests for scripts/trace-hypotheses.py — phase-3 hypothesis statistics (ticket 0243)."""

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location(
    "trace_hypotheses", SCRIPTS / "trace-hypotheses.py"
)
th = importlib.util.module_from_spec(spec)
spec.loader.exec_module(th)


def _row(**kw):
    base = {
        "project": "p",
        "session_id": "s1",
        "agent_id": "main",
        "model": "claude-opus-4-8",
        "turns": 10,
        "input_tokens": 100,
        "output_tokens": 100,
        "cache_read_input_tokens": 10_000,
        "cache_creation_input_tokens": 1_000,
        "cost_usd": 1.0,
        "read_only": False,
        "max_read_repeat": 1,
        "nav_turns": 0,
        "idle_turns": 0,
        "max_nav_run": 0,
        "merge_marker_turn": None,
        "verify_gaze_skills": 0,
        "entry_skill": "",
    }
    base.update(kw)
    return base


def test_zero_turn_rows_flagged_and_excluded():
    rows = [_row(), _row(session_id="s2", turns=0, cost_usd=0.0)]
    res = th.compute_all(rows)
    assert res["D1"]["zero_turn_agents"] == 1
    assert res["H6"]["total_usd"] == 1.0  # zero-turn row excluded


def test_h6_main_cost_share():
    rows = [
        _row(cost_usd=75.0),
        _row(session_id="s1", agent_id="agent-x", cost_usd=25.0),
    ]
    res = th.compute_all(rows)
    assert abs(res["H6"]["main_share"] - 0.75) < 1e-9


def test_h11_micro_turn_estimate():
    rows = [_row(turns=10, nav_turns=4, idle_turns=1, cost_usd=10.0)]
    res = th.compute_all(rows)
    assert abs(res["H11"]["micro_usd"] - 5.0) < 1e-9
    assert abs(res["H11"]["micro_share"] - 0.5) < 1e-9


def test_h10_post_delivery_tail():
    rows = [
        _row(turns=10, merge_marker_turn=8, cost_usd=10.0),
        _row(session_id="s2", cost_usd=5.0),  # no marker: not in tail stats
    ]
    res = th.compute_all(rows)
    assert abs(res["H10"]["tail_usd"] - 2.0) < 1e-9
    assert res["H10"]["sessions_with_marker"] == 1


def test_h13_verification_reentry():
    rows = [
        _row(verify_gaze_skills=3, cost_usd=50.0),
        _row(session_id="s2", verify_gaze_skills=1, cost_usd=7.0),
    ]
    res = th.compute_all(rows)
    assert res["H13"]["reentry_sessions"] == 1
    assert abs(res["H13"]["reentry_usd"] - 50.0) < 1e-9


def test_h3_readonly_drift():
    rows = [
        _row(agent_id="agent-a", read_only=True, turns=50, cost_usd=4.0),
        _row(agent_id="agent-b", read_only=True, turns=10, cost_usd=1.0),
        _row(agent_id="main", read_only=True, turns=99, cost_usd=9.0),  # mains excluded
    ]
    res = th.compute_all(rows)
    assert abs(res["H3"]["drift_usd"] - 4.0) < 1e-9


def test_h12_reread_cost():
    rows = [
        _row(max_read_repeat=4, cost_usd=6.0),
        _row(session_id="s2", max_read_repeat=1, cost_usd=3.0),
    ]
    res = th.compute_all(rows)
    assert abs(res["H12"]["reread_usd"] - 6.0) < 1e-9


def test_h2_loglog_exponent_recovers_power_law():
    rows = [_row(session_id=f"s{n}", turns=n, cost_usd=float(n**1.5)) for n in (2, 4, 8, 16, 32)]
    exp = th.fit_loglog(rows)
    assert abs(exp - 1.5) < 0.01


def test_load_census_types(tmp_path):
    import csv

    f = tmp_path / "census.csv"
    row = {k: ("" if v is None else v) for k, v in _row().items()}
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        w.writeheader()
        w.writerow(row)
    rows = th.load_census(f)
    assert rows[0]["turns"] == 10
    assert rows[0]["cost_usd"] == 1.0
    assert rows[0]["merge_marker_turn"] is None
    assert rows[0]["read_only"] is False


def test_cli_flags_present():
    src = (SCRIPTS / "trace-hypotheses.py").read_text()
    for flag in ("--census", "--output", "--compact-audit-json", "--pr-stats"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src
