"""Tests for scripts/trace_ab_decision.py — phase-5 A/B decision rule (ticket 0315).

Pre-registered decision rule: adopt a candidate config iff its cost is strictly
below baseline AND both guardrails (reroll_per_pr, escalate_count) hold within a
pre-registered noise band above baseline. A cost win with a breached guardrail
is a REJECT — the guardrail is binding.
"""

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location(
    "trace_ab_decision", SCRIPTS / "trace_ab_decision.py"
)
tad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tad)


def _metrics(cost_per_merged_pr=100.0, reroll_per_pr=0.30, escalate_count=18, **extra):
    m = {
        "cost_per_merged_pr": cost_per_merged_pr,
        "reroll_per_pr": reroll_per_pr,
        "escalate_count": escalate_count,
    }
    m.update(extra)
    return m


# --- decide() -------------------------------------------------------------


def test_adopt_when_cost_drops_and_guardrails_hold():
    baseline = _metrics(cost_per_merged_pr=100.0, reroll_per_pr=0.30, escalate_count=18)
    candidate = _metrics(cost_per_merged_pr=80.0, reroll_per_pr=0.30, escalate_count=18)
    res = tad.decide(baseline, candidate)
    assert res["verdict"] == "adopt", res["reasons"]


def test_reject_when_cost_not_below_baseline():
    baseline = _metrics(cost_per_merged_pr=100.0)
    candidate = _metrics(cost_per_merged_pr=100.0)  # perfect guardrails, no cost win
    res = tad.decide(baseline, candidate)
    assert res["verdict"] == "reject"
    assert any("cost" in r for r in res["reasons"])


def test_reject_on_guardrail_breach_despite_cost_win():
    # The binding-invariant case: cost wins big but a guardrail degrades.
    baseline = _metrics(cost_per_merged_pr=100.0, reroll_per_pr=0.30, escalate_count=18)
    candidate = _metrics(cost_per_merged_pr=50.0, reroll_per_pr=0.50, escalate_count=18)
    res = tad.decide(baseline, candidate)
    assert res["verdict"] == "reject"
    assert any("reroll_per_pr" in r for r in res["reasons"])


def test_boundary_exactly_at_noise_band_adopts_epsilon_over_rejects():
    # Band is baseline*(1+noise) with inclusive <=; parameterized, not hardcoded.
    noise = 0.05
    baseline = _metrics(cost_per_merged_pr=100.0, reroll_per_pr=0.40, escalate_count=20)
    # band = 0.40 * 1.05 ≈ 0.42 (float: 0.42000000000000004); 0.42 <= band holds
    at_band = _metrics(cost_per_merged_pr=90.0, reroll_per_pr=0.42, escalate_count=21)
    assert tad.decide(baseline, at_band, guardrail_noise_pct=noise)["verdict"] == "adopt"
    # epsilon over the band rejects
    over_band = _metrics(cost_per_merged_pr=90.0, reroll_per_pr=0.42001, escalate_count=21)
    res = tad.decide(baseline, over_band, guardrail_noise_pct=noise)
    assert res["verdict"] == "reject"


def test_reject_on_escalate_breach_only():
    baseline = _metrics(cost_per_merged_pr=100.0, reroll_per_pr=0.30, escalate_count=18)
    # escalate band at 10% = 19.8; 21 breaches. reroll fine, cost fine.
    candidate = _metrics(cost_per_merged_pr=80.0, reroll_per_pr=0.30, escalate_count=21)
    res = tad.decide(baseline, candidate)
    assert res["verdict"] == "reject"
    assert any("escalate_count" in r for r in res["reasons"])


def test_cost_key_selects_measure_b_metric():
    # Measure B compares on cost_per_cycle; cost_per_merged_pr must be ignored.
    baseline = _metrics(cost_per_merged_pr=100.0, cost_per_cycle=50.0)
    candidate = _metrics(cost_per_merged_pr=999.0, cost_per_cycle=40.0)
    res = tad.decide(baseline, candidate, cost_key="cost_per_cycle")
    assert res["verdict"] == "adopt"
    assert any("cost_per_cycle" in r for r in res["reasons"])


# --- filter_window() ------------------------------------------------------


def _row(date, **kw):
    base = {"date": date, "reroll": 1}
    base.update(kw)
    return base


def test_filter_window_inclusive_boundaries():
    rows = [
        _row("2026-06-01"),
        _row("2026-06-15"),
        _row("2026-06-30"),
        _row("2026-07-01"),
        _row("2026-05-31"),
    ]
    kept = tad.filter_window(rows, "2026-06-01", "2026-06-30")
    dates = {r["date"] for r in kept}
    assert dates == {"2026-06-01", "2026-06-15", "2026-06-30"}


def test_filter_window_custom_date_key():
    rows = [{"when": "2026-06-10"}, {"when": "2026-07-10"}]
    kept = tad.filter_window(rows, "2026-06-01", "2026-06-30", date_key="when")
    assert kept == [{"when": "2026-06-10"}]


def test_filter_window_matches_full_iso_timestamp_on_last_day():
    # A full ISO timestamp on the window's last day must not be dropped.
    rows = [_row("2026-06-30T14:00Z"), _row("2026-07-01T00:00Z")]
    kept = tad.filter_window(rows, "2026-06-01", "2026-06-30")
    assert [r["date"] for r in kept] == ["2026-06-30T14:00Z"]
