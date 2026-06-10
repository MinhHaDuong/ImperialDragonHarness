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


def test_h5_subagent_cache_write_priced_per_family():
    # Upper bound must price each subagent row at ITS family's 5m write rate:
    # fable bills 12.5/MTok — flat opus pricing (6.25) would understate it 2x.
    rows = [
        _row(agent_id="agent-f", model="claude-fable-5", cache_creation_input_tokens=1_000_000),
        _row(
            session_id="s2",
            agent_id="agent-o",
            model="claude-opus-4-8",
            cache_creation_input_tokens=1_000_000,
        ),
    ]
    res = th.compute_all(rows)
    assert abs(res["H5"]["subagent_cache_write_usd_upper"] - (12.5 + 6.25)) < 1e-6


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


def test_h8_reads_compact_audit_key(tmp_path):
    j = tmp_path / "compact.json"
    j.write_text('{"missed_runs": 64, "recoverable_usd_upper_bound": 1044.29}')
    res = th.merge_optional_inputs({"H4": {"verdict": "needs-data"}, "H8": {}}, j, None)
    assert res["H8"]["recoverable_usd_upper"] == 1044.29
    assert res["H8"]["missed_runs"] == 64


def test_cli_flags_present():
    src = (SCRIPTS / "trace-hypotheses.py").read_text()
    for flag in ("--census", "--output", "--compact-audit-json", "--pr-stats"):
        assert flag in src, f"missing CLI flag {flag}"
    assert "ArgumentParser" in src


# --- ticket 0244 refined statistics over disjoint buckets ---


def _row244(**kw):
    base = _row(
        merge_markers=0,
        merge_marker_turn_last=None,
        tail_turns=0,
        tail_mandated_turns=0,
        bucket_tail_cr=0,
        bucket_vg_cr=0,
        bucket_micro_cr=0,
        vg_second_turn=None,
        first_turn_cache_write=0,
        excess_file_reads=0,
        pr_numbers="",
    )
    base.update(kw)
    return base


def test_refined_tail_premium_subtracts_baseline():
    # opus: 100K tail cache_read over 2 tail turns, baseline 15K/turn
    rows = [
        _row244(
            tail_turns=2,
            tail_mandated_turns=1,
            bucket_tail_cr=100_000,
            merge_markers=1,
            merge_marker_turn_last=8,
        )
    ]
    res = th.compute_refined(rows, pr_join=None)
    expected = (100_000 - 2 * th.FRESH_BASELINE_TOKENS) * 0.5 / 1e6
    assert abs(res["H10r"]["premium_usd"] - expected) < 1e-9
    assert abs(res["H10r"]["mandated_share"] - 0.5) < 1e-9


def test_refined_micro_prices_bucket_exactly():
    rows = [_row244(bucket_micro_cr=200_000)]  # opus cache_read 0.5/MTok
    res = th.compute_refined(rows, pr_join=None)
    assert abs(res["H11r"]["micro_usd"] - 0.1) < 1e-9


def test_refined_buckets_are_additive_dedup():
    rows = [
        _row244(
            bucket_tail_cr=100_000,
            bucket_vg_cr=200_000,
            bucket_micro_cr=400_000,
            tail_turns=1,
            merge_markers=1,
            merge_marker_turn_last=1,
        )
    ]
    res = th.compute_refined(rows, pr_join=None)
    total = res["dedup"]["addressable_usd"]
    parts = res["H10r"]["tail_usd"] + res["H13r"]["vg_usd"] + res["H11r"]["micro_usd"]
    assert abs(total - parts) < 1e-9


def test_refined_h5_subagent_first_write_per_family():
    rows = [
        _row244(agent_id="agent-f", model="claude-fable-5", first_turn_cache_write=1_000_000),
        _row244(
            session_id="s2",
            agent_id="agent-o",
            model="claude-opus-4-8",
            first_turn_cache_write=1_000_000,
        ),
        _row244(session_id="s3", first_turn_cache_write=1_000_000),  # main: excluded
    ]
    res = th.compute_refined(rows, pr_join=None)
    assert abs(res["H5r"]["preamble_usd_upper"] - (12.5 + 6.25)) < 1e-6


def test_refined_reflexivity_sensitivity():
    rows = [
        _row244(
            cost_usd=10.0, pr_numbers="374", bucket_micro_cr=1_000_000, session_id="study"
        ),
        _row244(cost_usd=5.0, session_id="other", bucket_micro_cr=1_000_000),
    ]
    res = th.compute_refined(rows, pr_join=None, study_prs={374})
    assert res["reflexivity"]["study_sessions"] == 1
    assert (
        abs(res["reflexivity"]["micro_usd_excl_study"] - res["H11r"]["micro_usd"] / 2) < 1e-9
    )


def test_refined_h12_excess_read_bound():
    rows = [_row244(excess_file_reads=5)]  # opus: 5 x 2000 tok x 0.5/MTok
    res = th.compute_refined(rows, pr_join=None)
    expected = 5 * th.ASSUMED_READ_TOKENS * 0.5 / 1e6
    assert abs(res["H12r"]["reread_usd_upper"] - expected) < 1e-9


def test_refined_h4_quality_join():
    rows = [
        _row244(session_id="a", cost_usd=10.0, pr_numbers="1", verify_gaze_skills=2),
        _row244(session_id="b", cost_usd=2.0, pr_numbers="2"),
    ]
    pr_join = {
        ("ImperialDragonHarness", 1): {
            "additions": 900, "deletions": 100, "merged": True,
            "reroll_mentions": 2, "escalate_mentions": 0,
        },
        ("ImperialDragonHarness", 2): {
            "additions": 9, "deletions": 1, "merged": True,
            "reroll_mentions": 0, "escalate_mentions": 0,
        },
    }
    res = th.compute_refined(rows, pr_join=pr_join)
    assert res["H4r"]["joined_sessions"] == 2
    assert res["H4r"]["reentry_median_diff"] == 1000
    assert res["H4r"]["other_median_diff"] == 10
    assert res["quality"]["merged_rate"] == 1.0
