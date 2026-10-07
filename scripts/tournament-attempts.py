#!/usr/bin/env python3
"""Add observed attempt counts and retained generated-token means to a cleared snapshot.
All preserved attempts are deduplicated across top-level and nested run manifests.
No transcripts or prompts are exported. Counts include archived invalid/infra attempts;
these are not a model-only reliability estimate.
"""

import argparse
import json
import statistics
from pathlib import Path


def annotate(snapshot, arena):
    allowed = set(next(iter(snapshot["legs"].values())))
    allowed.update(t for legs in snapshot["legs"].values() for t in legs)
    attempts = {}
    by_source = {}
    for root in ("runs", "runs-void"):
        for path in (arena / root).rglob("run.json"):
            r = json.loads(path.read_text())
            ticket = r.get("ticket")
            if ticket not in allowed:
                continue
            source = str(path.relative_to(arena))
            by_source[source] = r
            key = (
                ticket,
                r.get("arm"),
                r.get("finished"),
                r.get("t0", {}).get("utc"),
                r.get("attempt"),
            )
            if key not in attempts or "attempts" not in path.parts:
                attempts[key] = {
                    "ticket": ticket,
                    "arm": r.get("arm"),
                    "verdict": r.get("verdict"),
                    "finished": r.get("finished"),
                    "output_tokens": r.get("tokens", {}).get("out_sum"),
                    "source": source,
                }
    measured = list(attempts.values())
    for arm, row in snapshot["arms"].items():
        family = {"m", "mr", "mb", "mo"} if arm in ("mi", "mr") else {arm}
        row["attempts_observed"] = sum(r["arm"] in family for r in measured)
        values = []
        for ticket, leg in snapshot["legs"][arm].items():
            if arm in ("mi", "mr"):
                rs = [
                    r
                    for r in snapshot["mistral_accounting"]["attempts"]
                    if r["ticket"] == ticket
                ]
                if arm == "mi":
                    rs = [
                        r
                        for r in rs
                        if r["verdict"] == "OK" and r["quality"] is not None
                    ]
                    preferred = [r for r in rs if not r.get("loop_failure")]
                    rs = (
                        [max(preferred or rs, key=lambda r: r["finished"])]
                        if rs
                        else []
                    )
                toks = [
                    by_source.get(r["source"], {}).get("tokens", {}).get("out_sum")
                    for r in rs
                ]
                value = sum(toks) if toks and all(t is not None for t in toks) else None
            else:
                value = (
                    by_source.get(f"runs/{ticket}-{arm}/run.json", {})
                    .get("tokens", {})
                    .get("out_sum")
                )
            if value is not None:
                values.append(value)
        row["output_tokens_mean"] = statistics.mean(values) if values else None
    snapshot["attempt_audit"] = {
        "scope": "All preserved attempts for the ten sampled tickets, including invalid infrastructure and wrong-base attempts. Mistral includes both providers for counts; token means follow the runs used for each graph series. Counts are not pure model reliability.",
        "records": measured,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--arena", type=Path, required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    a = p.parse_args()
    s = json.loads(a.snapshot.read_text())
    annotate(s, a.arena)
    a.snapshot.write_text(json.dumps(s, indent=2) + "\n")
    for arm, row in s["arms"].items():
        print(arm, row["attempts_observed"], row["output_tokens_mean"])


if __name__ == "__main__":
    main()
