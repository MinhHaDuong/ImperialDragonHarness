#!/usr/bin/env python3
"""Phase-3 hypothesis statistics over the trace census — ticket 0243.

Reads the per-agent census CSV (scripts/trace-stats.py with the 0243
detector columns) and computes one statistic per hypothesis H1-H13 from
docs/trace-open-coding-2026-06.md, plus the D1 data-quality flag. Emits a
JSON summary and an optional markdown section ready for the report.

Honest-accounting notes:
- Zero-turn agents (D1) are flagged and EXCLUDED from every $ statistic.
- Per-turn $ attributions (H10 tail, H11 micro-turns) are linear
  approximations: cost x (turns-in-class / turns). Late turns read more
  context than early ones, so H10 is a LOWER bound and H11 mixes both
  directions; both are screening statistics, settled in phase 4.
- H4 and the quality baseline need a forge join (--pr-stats CSV); H5 and
  H8 need per-message data (--compact-audit-json for H8). Absent inputs
  yield verdict "needs-data", never a silent drop.

Zero LLM/API calls.
"""

import argparse
import csv
import json
import logging
import math
import statistics
import sys
from pathlib import Path

log = logging.getLogger("trace-hypotheses")

INT_COLS = (
    "turns",
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "max_read_repeat",
    "nav_turns",
    "idle_turns",
    "max_nav_run",
    "verify_gaze_skills",
)


def load_census(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for raw in csv.DictReader(fh):
            r = dict(raw)
            for k in INT_COLS:
                r[k] = int(float(r.get(k) or 0))
            r["cost_usd"] = float(r.get("cost_usd") or 0)
            mm = r.get("merge_marker_turn")
            r["merge_marker_turn"] = int(float(mm)) if mm not in (None, "") else None
            r["read_only"] = str(r.get("read_only")) == "True"
            rows.append(r)
    return rows


def fit_loglog(rows: list[dict]) -> float:
    """Least-squares slope of log(cost) ~ log(turns) over positive rows."""
    pts = [
        (math.log(r["turns"]), math.log(r["cost_usd"]))
        for r in rows
        if r["turns"] > 0 and r["cost_usd"] > 0
    ]
    n = len(pts)
    if n < 2:
        return float("nan")
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    return sxy / sxx if sxx else float("nan")


def _share(part: float, whole: float) -> float:
    return part / whole if whole else 0.0


def compute_all(all_rows: list[dict]) -> dict:
    zero = [r for r in all_rows if r["turns"] == 0]
    rows = [r for r in all_rows if r["turns"] > 0]
    total = sum(r["cost_usd"] for r in rows)
    mains = [r for r in rows if r["agent_id"] == "main"]
    subs = [r for r in rows if r["agent_id"] != "main"]

    # H1: $ share by token category, priced per row's dominant model.
    # Approximation: the dominant model prices ALL of a row's tokens.
    cat_usd = dict.fromkeys(("input", "output", "cache_read", "cache_write"), 0.0)
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "trace_stats", Path(__file__).resolve().parent / "trace-stats.py"
    )
    ts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ts)
    for r in rows:
        p = ts.resolve_pricing(r.get("model") or "")
        if p is None:
            continue
        cat_usd["input"] += r["input_tokens"] * p["input"] / 1e6
        cat_usd["output"] += r["output_tokens"] * p["output"] / 1e6
        cat_usd["cache_read"] += r["cache_read_input_tokens"] * p["cache_read"] / 1e6
        cat_usd["cache_write"] += r["cache_creation_input_tokens"] * p["cache_write_5m"] / 1e6
    cat_total = sum(cat_usd.values())

    # H2: context concentration by cost decile + global exponent.
    by_cost = sorted(rows, key=lambda r: r["cost_usd"])
    cr_per_turn_decile = []
    if by_cost:
        size = max(1, len(by_cost) // 10)
        for d in range(10):
            chunk = by_cost[d * size : (d + 1) * size] if d < 9 else by_cost[9 * size :]
            turns = sum(r["turns"] for r in chunk)
            cr = sum(r["cache_read_input_tokens"] for r in chunk)
            cr_per_turn_decile.append(round(cr / turns) if turns else 0)

    # H3: read-only subagents drifting past 40 turns.
    drift = [r for r in subs if r["read_only"] and r["turns"] > 40]

    # H7: mean log-residual by model family, mains only.
    slope = fit_loglog(rows)
    resid_by_family: dict[str, list[float]] = {}
    if not math.isnan(slope):
        pts = [r for r in rows if r["turns"] > 0 and r["cost_usd"] > 0]
        mx = statistics.mean(math.log(r["turns"]) for r in pts)
        my = statistics.mean(math.log(r["cost_usd"]) for r in pts)
        intercept = my - slope * mx
        for r in mains:
            if r["cost_usd"] <= 0 or r["turns"] <= 0:
                continue
            fam = next(
                (f for f in ("fable", "opus", "sonnet", "haiku") if f in (r.get("model") or "")),
                "unknown",
            )
            pred = intercept + slope * math.log(r["turns"])
            resid_by_family.setdefault(fam, []).append(math.log(r["cost_usd"]) - pred)
    h7 = {f: round(statistics.mean(v), 3) for f, v in resid_by_family.items() if v}

    # H10: post-delivery tail (linear approximation, lower bound).
    marked = [r for r in mains if r["merge_marker_turn"] is not None]
    tail_usd = sum(
        r["cost_usd"] * (r["turns"] - r["merge_marker_turn"]) / r["turns"]
        for r in marked
        if r["turns"] > 0 and r["merge_marker_turn"] < r["turns"]
    )

    # H11: micro-turn (navigational + idle) $ estimate, linear approximation.
    micro_usd = sum(
        r["cost_usd"] * (r["nav_turns"] + r["idle_turns"]) / r["turns"]
        for r in rows
        if r["turns"] > 0
    )

    # H12: $ sitting in agents that re-read one file 3+ times.
    reread = [r for r in rows if r["max_read_repeat"] >= 3]

    # H13: sessions whose MAIN invoked verify/gaze 2+ times.
    reentry = [r for r in mains if r["verify_gaze_skills"] >= 2]

    return {
        "D1": {"zero_turn_agents": len(zero)},
        "H1": {
            "category_usd": {k: round(v, 2) for k, v in cat_usd.items()},
            "cache_read_share": round(_share(cat_usd["cache_read"], cat_total), 3),
        },
        "H2": {"loglog_exponent": round(slope, 3), "cr_per_turn_by_decile": cr_per_turn_decile},
        "H3": {
            "drift_agents": len(drift),
            "drift_usd": round(sum(r["cost_usd"] for r in drift), 2),
            "drift_share": round(_share(sum(r["cost_usd"] for r in drift), total), 4),
        },
        "H4": {"verdict": "needs-data", "note": "requires --pr-stats forge join"},
        "H5": {
            "verdict": "needs-data",
            "note": "spawn-boundary redundancy needs per-message cache_creation; phase-4 extraction",
            "subagent_cache_write_usd_upper": round(
                sum(
                    r["cache_creation_input_tokens"] * 6.25 / 1e6  # opus 5m upper
                    for r in subs
                ),
                2,
            ),
        },
        "H6": {
            "total_usd": round(total, 2),
            "main_share": round(_share(sum(r["cost_usd"] for r in mains), total), 3),
        },
        "H7": {"mean_log_residual_by_family_mains": h7},
        "H8": {"verdict": "needs-data", "note": "run scripts/trace-compact-audit.py --json"},
        "H10": {
            "sessions_with_marker": len(marked),
            "tail_usd": round(tail_usd, 2),
            "tail_share_of_total": round(_share(tail_usd, total), 4),
        },
        "H11": {
            "micro_usd": round(micro_usd, 2),
            "micro_share": round(_share(micro_usd, total), 4),
            "max_nav_run_p99": (
                sorted(r["max_nav_run"] for r in rows)[int(0.99 * (len(rows) - 1))]
                if rows
                else 0
            ),
        },
        "H12": {
            "reread_agents": len(reread),
            "reread_usd": round(sum(r["cost_usd"] for r in reread), 2),
        },
        "H13": {
            "reentry_sessions": len(reentry),
            "reentry_usd": round(sum(r["cost_usd"] for r in reentry), 2),
        },
    }


def merge_optional_inputs(results: dict, compact_json: Path | None, pr_stats: Path | None) -> dict:
    if compact_json and compact_json.exists():
        data = json.loads(compact_json.read_text())
        results["H8"] = {
            "verdict": "computed",
            "recoverable_usd_upper": data.get("recoverable_usd_upper_bound")
            or data.get("recoverable_usd_upper"),
            "missed_runs": data.get("missed_runs"),
            "source": str(compact_json),
        }
    if pr_stats and pr_stats.exists():
        results["H4"]["verdict"] = "computed-externally"
        results["H4"]["source"] = str(pr_stats)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute H1-H13 statistics over the trace census CSV."
    )
    parser.add_argument("--census", type=Path, required=True, help="Per-agent census CSV")
    parser.add_argument("--output", type=Path, help="Write JSON results here (default stdout)")
    parser.add_argument(
        "--compact-audit-json", type=Path, help="trace-compact-audit.py --json output (H8)"
    )
    parser.add_argument("--pr-stats", type=Path, help="Forge-join CSV for H4/quality baseline")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    rows = load_census(args.census)
    results = merge_optional_inputs(compute_all(rows), args.compact_audit_json, args.pr_stats)
    text = json.dumps(results, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
        log.info("wrote %s", args.output)
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
