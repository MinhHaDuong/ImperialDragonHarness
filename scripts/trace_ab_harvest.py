#!/usr/bin/env python3
"""Phase-5 A/B offline harvest — ticket 0326 (child of 0245, trace-doctor phase 5).

Computes the pre-registered metrics (docs/trace-ab-2026-06.md) for one arm from
cached census + join inputs and routes a baseline/candidate pair through the
pre-registered decision rule in scripts/trace_ab_decision.py. This is the
offline tooling the live A/B arms on ticket 0245 will consume once they run;
it collects no data and writes no verdict of its own.

STRICT invariants (0245): zero LLM calls, zero network, no edits to
trace-stats.py / trace-hypotheses.py / trace-pr-join.py (import/reuse only,
additive discipline). Outputs carry only aggregates and PR numbers — never
trace content.

Inputs:
  - census CSV  — per-agent rows from `scripts/trace-stats.py --output` (the
    columns read: `project`, `agent_id`, `pr_numbers`, `cost_usd`, `date`,
    `verify_gaze_skills`).
  - join cache CSV — `docs/trace-pr-join-2026-06.csv`, produced by
    `scripts/trace-pr-join.py` (`repo`, `pr`, `merged`, `reroll_mentions`,
    `escalate_mentions`).

Metric definitions (see docs/trace-ab-2026-06.md § Metric definitions):
  - cost_per_merged_pr — total shadow-$ in the arm / merged PR count (primary).
  - cost_per_cycle     — total shadow-$ / gaze/verify cycle count (measure B).
  - reroll_per_pr      — REROLL mentions / PR (guardrail; baseline 33/112).
  - escalate_count     — ESCALATE mentions in the arm (guardrail; baseline 18).
"""

import argparse
import csv
import importlib.util
import json
import logging
import math
from pathlib import Path

log = logging.getLogger("trace-ab-harvest")

_HERE = Path(__file__).resolve().parent


def _load_sibling(mod_name: str, filename: str):
    """Import a sibling script by path (works for hyphenated filenames too).

    Additive discipline: the harvest reuses the committed decision rule and the
    join's project→repo / pair-collection helpers rather than reimplementing
    them, and never edits those modules.
    """
    spec = importlib.util.spec_from_file_location(mod_name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Reused, never edited: the pre-registered decision rule and the forge-join
# helpers. `decide` / `filter_window` / `PREREGISTERED_NOISE_PCT` are the
# 0315 pre-registration; `project_to_repo` / `collect_pairs` map census rows
# to (repo, pr) pairs exactly as the join does.
_decision = _load_sibling("trace_ab_decision", "trace_ab_decision.py")
_join = _load_sibling("trace_pr_join", "trace-pr-join.py")

decide = _decision.decide
filter_window = _decision.filter_window
PREREGISTERED_NOISE_PCT = _decision.PREREGISTERED_NOISE_PCT
project_to_repo = _join.project_to_repo
collect_pairs = _join.collect_pairs


def load_census(path: Path) -> list[dict]:
    """Read a trace-stats census CSV into a list of row dicts (strings)."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_join(path: Path) -> dict[tuple[str, int], dict]:
    """Read the forge-join cache CSV, keyed by (repo, int(pr)).

    Mirrors trace-pr-join's own cache keying so `collect_pairs` output indexes
    straight into this dict.
    """
    join: dict[tuple[str, int], dict] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            join[(r["repo"], int(r["pr"]))] = r
    return join


def _as_int(value) -> int | None:
    """Parse a join cell to int; blank/None (unresolved PR) -> None."""
    if value in (None, ""):
        return None
    return int(value)


def compute_metrics(
    census_rows: list[dict],
    join: dict[tuple[str, int], dict],
    *,
    window: tuple[str, str] | None = None,
) -> dict:
    """Compute the pre-registered metrics for one arm.

    `census_rows` are trace-stats rows; `join` is the forge-join cache keyed by
    (repo, int(pr)). When `window` is given the census is sliced to
    [start, end] (inclusive) with the pre-registered `filter_window` before any
    aggregation — this is the measure-B path; measure A is ticket-keyed and
    passes no window.

    Returns the metric dict the decision rule consumes plus provenance counts
    (`n_pairs`, `n_merged`, `total_cost`, `total_cycles`). A cost metric with no
    denominator (no merged PR / no cycle) is `math.inf` so it never spuriously
    reads as a cost win.
    """
    rows = filter_window(census_rows, window[0], window[1]) if window else census_rows

    total_cost = sum(float(r.get("cost_usd") or 0.0) for r in rows)
    total_cycles = sum(int(r.get("verify_gaze_skills") or 0) for r in rows)

    pairs = collect_pairs(rows)
    n_merged = reroll = escalate = 0
    for pair in pairs:
        j = join.get(pair)
        if j is None:
            continue
        if str(j.get("merged")) == "True":
            n_merged += 1
        r_mentions = _as_int(j.get("reroll_mentions"))
        if r_mentions is not None:
            reroll += r_mentions
        e_mentions = _as_int(j.get("escalate_mentions"))
        if e_mentions is not None:
            escalate += e_mentions

    n_pairs = len(pairs)
    return {
        "cost_per_merged_pr": total_cost / n_merged if n_merged else math.inf,
        "cost_per_cycle": total_cost / total_cycles if total_cycles else math.inf,
        "reroll_per_pr": reroll / n_pairs if n_pairs else 0.0,
        "escalate_count": escalate,
        "n_pairs": n_pairs,
        "n_merged": n_merged,
        "total_cost": round(total_cost, 4),
        "total_cycles": total_cycles,
    }


def _window_arg(value: str) -> tuple[str, str]:
    start, _, end = value.partition(":")
    if not start or not end:
        raise argparse.ArgumentTypeError("window must be START:END, e.g. 2026-06-01:2026-06-30")
    return start, end


def harvest(
    baseline_census: Path,
    candidate_census: Path,
    join_cache: Path,
    *,
    baseline_window: tuple[str, str] | None = None,
    candidate_window: tuple[str, str] | None = None,
    cost_key: str = "cost_per_merged_pr",
) -> dict:
    """Compute both arms' metrics and route them through the decision rule."""
    join = load_join(join_cache)
    baseline = compute_metrics(load_census(baseline_census), join, window=baseline_window)
    candidate = compute_metrics(load_census(candidate_census), join, window=candidate_window)
    verdict = decide(baseline, candidate, cost_key=cost_key)
    return {"baseline": baseline, "candidate": candidate, **verdict, "cost_key": cost_key}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline harvest of the pre-registered phase-5 A/B metrics.",
    )
    parser.add_argument(
        "--baseline-census", type=Path, required=True, help="Baseline-arm census CSV"
    )
    parser.add_argument(
        "--candidate-census", type=Path, required=True, help="Candidate-arm census CSV"
    )
    parser.add_argument(
        "--join-cache",
        type=Path,
        default=_HERE.parent / "docs" / "trace-pr-join-2026-06.csv",
        help="Forge-join cache CSV (default: docs/trace-pr-join-2026-06.csv)",
    )
    parser.add_argument(
        "--baseline-window",
        type=_window_arg,
        default=None,
        help="Slice the baseline census to START:END (inclusive). Omit for measure A.",
    )
    parser.add_argument(
        "--candidate-window",
        type=_window_arg,
        default=None,
        help="Slice the candidate census to START:END (inclusive). Omit for measure A.",
    )
    parser.add_argument(
        "--cost-key",
        choices=("cost_per_merged_pr", "cost_per_cycle"),
        default="cost_per_merged_pr",
        help="Primary cost metric: cost_per_merged_pr (measure A) or cost_per_cycle (measure B).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the full result as JSON to stdout"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    result = harvest(
        args.baseline_census,
        args.candidate_census,
        args.join_cache,
        baseline_window=args.baseline_window,
        candidate_window=args.candidate_window,
        cost_key=args.cost_key,
    )

    log.info("verdict: %s (cost_key=%s)", result["verdict"], result["cost_key"])
    for reason in result["reasons"]:
        log.info("  %s", reason)
    if args.json:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
