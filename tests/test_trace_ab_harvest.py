"""Tests for scripts/trace_ab_harvest.py — phase-5 A/B offline harvest (ticket 0326).

The harvest CLI computes the pre-registered metrics (cost_per_merged_pr,
cost_per_cycle, reroll_per_pr, escalate_count) from cached census + join inputs
and routes them through decide()/filter_window() in trace_ab_decision.py. These
tests build fixtures that reproduce the phase-4 guardrail baselines VERBATIM
(REROLL/PR 33/112, ESCALATE 18) and check that computed metric values map to the
expected adopt/reject verdict through the full harvest path.

Pure Python, no heavy deps, no network, no subprocess — fast tier.
"""

import csv
import importlib.util
import math
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location(
    "trace_ab_harvest", SCRIPTS / "trace_ab_harvest.py"
)
hv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hv)


# --- fixtures -------------------------------------------------------------

# Phase-4 guardrail baselines, used verbatim (docs/trace-counterfactuals-2026-06.md).
BASELINE_PAIRS = 112
BASELINE_REROLL = 33
BASELINE_ESCALATE = 18


def _arm(n_pairs, n_reroll, n_escalate, total_cost, *, cycles_per_pr=1, start_pr=1000):
    """Build (census_rows, join) for an arm of `n_pairs` merged PRs.

    Each census row is a distinct main-agent session citing one PR; cost is
    spread evenly. The join dict carries `n_reroll` total REROLL mentions and
    `n_escalate` total ESCALATE mentions distributed one-per-PR from the front.
    """
    census: list[dict] = []
    join: dict[tuple[str, int], dict] = {}
    per_pr_cost = total_cost / n_pairs
    for i in range(n_pairs):
        pr = start_pr + i
        census.append(
            {
                "project": "-home-haduong-padme",
                "agent_id": "main",
                "pr_numbers": str(pr),
                "cost_usd": f"{per_pr_cost}",
                "date": "2026-06-15",
                "verify_gaze_skills": str(cycles_per_pr),
            }
        )
        join[("padme", pr)] = {
            "repo": "padme",
            "pr": pr,
            "merged": "True",
            "reroll_mentions": str(1 if i < n_reroll else 0),
            "escalate_mentions": str(1 if i < n_escalate else 0),
        }
    return census, join


def _baseline():
    # cost 1120 over 112 merged PRs -> cost_per_merged_pr = 10.0
    return _arm(BASELINE_PAIRS, BASELINE_REROLL, BASELINE_ESCALATE, 1120.0)


# --- compute_metrics reproduces the pre-registered baselines --------------


def test_compute_metrics_reproduces_phase4_baselines():
    census, join = _baseline()
    m = hv.compute_metrics(census, join)
    assert m["reroll_per_pr"] == BASELINE_REROLL / BASELINE_PAIRS
    assert m["escalate_count"] == BASELINE_ESCALATE
    assert m["n_pairs"] == BASELINE_PAIRS
    assert m["n_merged"] == BASELINE_PAIRS
    assert m["cost_per_merged_pr"] == 10.0


def test_cost_per_cycle_uses_verify_gaze_column():
    census, join = _arm(10, 0, 0, 200.0, cycles_per_pr=2)  # 20 cycles, $200
    m = hv.compute_metrics(census, join)
    assert m["cost_per_cycle"] == 10.0


def test_no_merged_pr_yields_infinite_cost():
    census, join = _arm(3, 0, 0, 30.0)
    for j in join.values():
        j["merged"] = "False"
    m = hv.compute_metrics(census, join)
    assert math.isinf(m["cost_per_merged_pr"])
    assert m["n_merged"] == 0


# --- full harvest path: metric values -> adopt/reject verdict -------------


def test_adopt_when_cost_drops_and_guardrails_hold():
    base_census, base_join = _baseline()
    baseline = hv.compute_metrics(base_census, base_join)
    # Candidate: half the cost per PR, guardrail ratios at or below baseline.
    cand_census, cand_join = _arm(56, 16, 18, 280.0, start_pr=5000)  # 16/56 < 33/112
    candidate = hv.compute_metrics(cand_census, cand_join)
    res = hv.decide(baseline, candidate)
    assert res["verdict"] == "adopt", res["reasons"]


def test_reject_on_reroll_breach_despite_cost_win():
    base_census, base_join = _baseline()
    baseline = hv.compute_metrics(base_census, base_join)
    # 20/56 = 0.357 > baseline 0.2946 * 1.10 = 0.324 band: guardrail breach.
    cand_census, cand_join = _arm(56, 20, 18, 140.0, start_pr=5000)
    candidate = hv.compute_metrics(cand_census, cand_join)
    res = hv.decide(baseline, candidate)
    assert res["verdict"] == "reject"
    assert any("reroll_per_pr" in r for r in res["reasons"])


def test_reject_on_escalate_breach_despite_cost_win():
    base_census, base_join = _baseline()
    baseline = hv.compute_metrics(base_census, base_join)
    # escalate 22 > baseline 18 * 1.10 = 19.8: breach; reroll and cost fine.
    cand_census, cand_join = _arm(56, 16, 22, 280.0, start_pr=5000)
    candidate = hv.compute_metrics(cand_census, cand_join)
    res = hv.decide(baseline, candidate)
    assert res["verdict"] == "reject"
    assert any("escalate_count" in r for r in res["reasons"])


def test_measure_b_cost_key_is_cost_per_cycle():
    base_census, base_join = _arm(20, 0, 0, 400.0, cycles_per_pr=2)  # 40 cycles, $10/cycle
    baseline = hv.compute_metrics(base_census, base_join)
    cand_census, cand_join = _arm(20, 0, 0, 320.0, cycles_per_pr=2, start_pr=7000)  # $8/cycle
    candidate = hv.compute_metrics(cand_census, cand_join)
    res = hv.decide(baseline, candidate, cost_key="cost_per_cycle")
    assert res["verdict"] == "adopt", res["reasons"]
    assert any("cost_per_cycle" in r for r in res["reasons"])


# --- windowing ------------------------------------------------------------


def test_window_slices_census_before_metrics():
    census, join = _arm(4, 0, 0, 40.0)
    census[0]["date"] = "2026-05-01"  # out of window
    census[1]["date"] = "2026-07-10"  # out of window
    census[2]["date"] = "2026-06-10"  # in
    census[3]["date"] = "2026-06-20"  # in
    m = hv.compute_metrics(census, join, window=("2026-06-01", "2026-06-30"))
    assert m["n_pairs"] == 2
    assert m["n_merged"] == 2


# --- CSV loaders round-trip -----------------------------------------------


def test_load_census_and_join_round_trip(tmp_path):
    census, join = _arm(3, 1, 1, 30.0)
    census_path = tmp_path / "census.csv"
    with open(census_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(census[0].keys()))
        w.writeheader()
        w.writerows(census)

    join_path = tmp_path / "join.csv"
    with open(join_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["repo", "pr", "merged", "reroll_mentions", "escalate_mentions"]
        )
        w.writeheader()
        for row in join.values():
            w.writerow(row)

    loaded_census = hv.load_census(census_path)
    loaded_join = hv.load_join(join_path)
    m = hv.compute_metrics(loaded_census, loaded_join)
    assert m["n_pairs"] == 3
    assert m["reroll_per_pr"] == 1 / 3
    assert m["escalate_count"] == 1
