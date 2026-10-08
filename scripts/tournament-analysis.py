#!/usr/bin/env python3
"""Analyze cumulative arena results without conditioning on success.

Read-only. Quota/provider failures and unsettled panels remain pending.
Costs are API USD or registered local electricity converted at 1.08 USD/EUR.
"""

import argparse
import json
from pathlib import Path
import statistics

LOCAL = {"a", "b", "b2", "b3", "c", "c2"}
ELEC_USD_S = 0.23 * 0.6 * 1.08 / 3600
# Arms whose legs sit outside the frozen matrix: cycle-1 d/e, and n (Haiku 5.5),
# launched on 2026-10-08 after the matrix was written.
OFF_MATRIX = {"d", "e", "n"}
# Model lineage per arm, independent of the provider or door that serves it:
# hosted and local Qwen are one family, OpenRouter-served GLM is GLM.
FAMILY = {
    "a": "Qwen",
    "b2": "Qwen",
    "b3": "Qwen",
    "c": "Qwen",
    "c2": "Qwen",
    "d": "Anthropic",
    "d2": "Anthropic",
    "e2": "OpenAI",
    "e3": "OpenAI",
    "f": "GLM",
    "g": "Anthropic",
    "i": "DeepSeek",
    "j": "GLM",
    "k": "Xiaomi",
    "l": "OpenAI",
    "n": "Anthropic",
}


def read_leg(directory, arm):
    path = directory / "run.json"
    if not path.exists():
        return {"state": "pending"}
    record = json.loads(path.read_text())
    # Inspect errors without emitting raw messages (which can contain key URLs).
    for session in directory.glob("attempts/*/sessions/*.jsonl"):
        for line in session.read_text().splitlines():
            event = json.loads(line)
            message = event.get("message", {})
            if message.get("stopReason") == "error" and record.get("verdict") != "OK":
                return {"state": "infrastructure"}
    verdict = record.get("verdict")
    if verdict not in {"OK", "DNF", "VOID-EMPTY"}:
        return {"state": "pending"}
    if verdict == "OK":
        scores = []
        for path in (directory / "judges").glob("*.json"):
            parsed = json.loads(path.read_text()).get("parsed")
            score = parsed.get("score") if isinstance(parsed, dict) else None
            if (
                isinstance(score, (int, float))
                and not isinstance(score, bool)
                and 0 <= score <= 10
            ):
                scores.append(score)
        if len(scores) != 3:
            return {"state": "pending"}
        quality = sum(scores)
    else:
        quality = 0
    seconds = record.get("seconds")
    cost = record.get("cost_usd")
    if cost is None:
        cost = record.get("cost_usd_legacy")
    if arm in LOCAL and seconds is not None:
        cost = seconds * ELEC_USD_S
    return {
        "state": "ok" if verdict == "OK" else "failure",
        "quality": quality,
        "seconds": seconds,
        "cost_usd": cost,
    }


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def analyze(arena):
    matrix = json.loads((arena / "runs.json").read_text())["matrix"]
    expected = {
        (row["ticket"], arm) for row in matrix for arm in row["arm_order"] if arm != "h"
    }
    # Cycles are additive: retain the off-matrix identities; preliminary 0188 is excluded.
    expected |= {
        (p.name.rsplit("-", 1)[0], p.name.rsplit("-", 1)[1])
        for p in (arena / "runs").iterdir()
        if p.is_dir()
        and p.name.rsplit("-", 1)[1] in OFF_MATRIX
        and not p.name.startswith("0188-")
    }
    legs = {
        (t, a): read_leg(arena / "runs" / f"{t}-{a}", a) for t, a in sorted(expected)
    }
    summary = {}
    for arm in sorted({a for _, a in expected}):
        rows = [r for (t, a), r in legs.items() if a == arm]
        valid = [r for r in rows if r["state"] in {"ok", "failure"}]
        summary[arm] = {
            "expected": len(rows),
            "evaluated": len(valid),
            "ok": sum(r["state"] == "ok" for r in rows),
            "failures": sum(r["state"] == "failure" for r in rows),
            "pending": sum(r["state"] not in {"ok", "failure"} for r in rows),
            "quality_median": median([r["quality"] for r in valid]),
            "quality_mean": statistics.mean(r["quality"] for r in valid)
            if valid
            else None,
            "seconds_median": median([r["seconds"] for r in valid]),
            "cost_usd_median": median([r["cost_usd"] for r in valid]),
            "time_observed": sum(r["seconds"] is not None for r in valid),
            "cost_observed": sum(r["cost_usd"] is not None for r in valid),
            "final": len(valid) == len(rows),
        }
    pairs = {}
    for a in summary:
        for b in summary:
            if a >= b:
                continue
            common = [
                (legs[t, a], legs[t, b])
                for t in sorted({t for t, x in legs if x == a})
                if (t, b) in legs
                and legs[t, a]["state"] in {"ok", "failure"}
                and legs[t, b]["state"] in {"ok", "failure"}
            ]
            pairs[f"{a}/{b}"] = {
                "n": len(common),
                "quality_wins": sum(x["quality"] > y["quality"] for x, y in common),
                "quality_ties": sum(x["quality"] == y["quality"] for x, y in common),
                "quality_losses": sum(x["quality"] < y["quality"] for x, y in common),
                "quality_difference_median": median(
                    [x["quality"] - y["quality"] for x, y in common]
                ),
                "time_pairs": sum(
                    x["seconds"] is not None and y["seconds"] is not None
                    for x, y in common
                ),
                "faster": sum(
                    x["seconds"] < y["seconds"]
                    for x, y in common
                    if x["seconds"] is not None and y["seconds"] is not None
                ),
                "cost_pairs": sum(
                    x["cost_usd"] is not None and y["cost_usd"] is not None
                    for x, y in common
                ),
                "cheaper": sum(
                    x["cost_usd"] < y["cost_usd"]
                    for x, y in common
                    if x["cost_usd"] is not None and y["cost_usd"] is not None
                ),
            }
    eligible = {
        a: r
        for a, r in summary.items()
        if r["final"]
        and r["time_observed"] == r["expected"]
        and r["cost_observed"] == r["expected"]
    }

    def dominates(x, y):
        return (
            x["quality_median"] >= y["quality_median"]
            and x["seconds_median"] <= y["seconds_median"]
            and x["cost_usd_median"] <= y["cost_usd_median"]
            and any(
                x[k] != y[k]
                for k in ["quality_median", "seconds_median", "cost_usd_median"]
            )
        )

    frontier = [
        a
        for a, r in eligible.items()
        if not any(dominates(v, r) for b, v in eligible.items() if b != a)
    ]
    return {
        "pareto_complete_arms_only": frontier,
        "method": "Model failures score zero; consumed time/cost retained. Infrastructure and unsettled panels pending. Cycles additive; h and preliminaries excluded.",
        "arms": summary,
        "pairs": pairs,
    }


def refresh_grid(grid, report):
    """Refresh numeric fields and the lineage family of each grid row by arm."""
    for row in grid["grid"]:
        result = report["arms"][row["arm"]]
        row["family"] = FAMILY[row["arm"]]
        row["coverage"] = result
        state = "final" if result["final"] else "provisional"
        row["quality"] = (
            f"{result['quality_median']:.2f} ({state}, "
            f"failures={result['failures']}/{result['expected']})"
        )
        row["time"] = (
            f"{result['seconds_median'] / 60:.2f} min"
            if result["seconds_median"] is not None
            else "pending"
        )
        row["cost"] = (
            f"{result['cost_usd_median']:.4f} USD"
            if result["cost_usd_median"] is not None
            else "pending"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", type=Path, default=Path.home() / "arena")
    parser.add_argument(
        "--grid",
        type=Path,
        help="Refresh numeric fields and family of an existing grid by its arm identifiers",
    )
    args = parser.parse_args()
    report = analyze(args.arena)
    if args.grid:
        grid = json.loads(args.grid.read_text())
        refresh_grid(grid, report)
        args.grid.write_text(json.dumps(grid, indent=2) + "\n")
    print(json.dumps(report, indent=2))
