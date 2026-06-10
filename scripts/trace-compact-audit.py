#!/usr/bin/env python3
"""Missed compact/clear opportunity detector — ticket 0239, trace-doctor phase 2a.

Walks the session-trace corpus and, per agent, extracts the per-turn
cache_read trajectory (unique message.id order, same dedupe rule as
scripts/trace-stats.py) plus the positions of compaction boundaries
(`type: "system"` / `subtype: "compact_boundary"`) and `/clear` commands.

A *missed opportunity* is a run of >= --min-run consecutive turns whose
per-turn cache_read stays >= --threshold, uninterrupted by any compact or
clear. The recoverable $ is an UPPER BOUND counterfactual: had the agent
compacted at the start of the run, every later turn in the run would have
read the post-compact median context (observed across sessions that DID
compact) instead of its actual cache_read. Context re-growth after the
hypothetical compaction is ignored — hence upper bound.

Zero LLM/API calls; emits aggregates only, never trace content.
"""

import argparse
import csv
import importlib.util
import json
import logging
import re
import statistics
import sys
from pathlib import Path

log = logging.getLogger("trace-compact-audit")

# Reuse the census module (pricing, dedupe conventions, corpus walker).
_TS_SPEC = importlib.util.spec_from_file_location(
    "trace_stats", Path(__file__).resolve().parent / "trace-stats.py"
)
ts = importlib.util.module_from_spec(_TS_SPEC)
_TS_SPEC.loader.exec_module(ts)

CLEAR_RE = re.compile(r"<command-name>/?clear</command-name>")

# Used only if the corpus contains no compaction to take a median from.
DEFAULT_POST_COMPACT_TOKENS = 20_000


def parse_trajectory(path: Path) -> dict:
    """Parse one trace into an ordered event stream.

    Events: {"kind": "turn", "cache_read": int, "model": str},
    {"kind": "compact"}, {"kind": "clear"}. Turns are deduped by
    message.id; <synthetic> records are not turns. Also collects the
    cache_read of the first turn after each compaction
    (post_compact_reads) and the boundary's own postTokens
    (post_compact_tokens) — both feed the corpus-wide median.
    """
    events: list[dict] = []
    seen_ids: set[str] = set()
    post_compact_reads: list[int] = []
    post_compact_tokens: list[int] = []
    awaiting_post_read = False
    entry_skill = None
    last_ts = None

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue

            tstamp = ts._parse_ts(rec.get("timestamp", ""))
            if tstamp is not None:
                last_ts = tstamp

            rec_type = rec.get("type")
            if rec_type == "system" and rec.get("subtype") == "compact_boundary":
                events.append({"kind": "compact"})
                meta = rec.get("compactMetadata") or {}
                if isinstance(meta.get("postTokens"), int):
                    post_compact_tokens.append(meta["postTokens"])
                awaiting_post_read = True
                continue

            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")

            if rec_type == "assistant":
                msg_id = msg.get("id")
                usage = msg.get("usage")
                model = msg.get("model") or ""
                if (
                    msg_id
                    and msg_id not in seen_ids
                    and isinstance(usage, dict)
                    and model != "<synthetic>"
                ):
                    seen_ids.add(msg_id)
                    cache_read = usage.get("cache_read_input_tokens", 0) or 0
                    events.append(
                        {"kind": "turn", "cache_read": cache_read, "model": model}
                    )
                    if awaiting_post_read:
                        post_compact_reads.append(cache_read)
                        awaiting_post_read = False
            elif rec_type == "user":
                if isinstance(content, str):
                    if CLEAR_RE.search(content):
                        events.append({"kind": "clear"})
                    elif entry_skill is None:
                        for m in re.finditer(
                            r"<command-name>/?([\w-]+)</command-name>", content
                        ):
                            if m.group(1) not in ts.BUILTIN_COMMANDS:
                                entry_skill = m.group(1)
                                break

    return {
        "events": events,
        "post_compact_reads": post_compact_reads,
        "post_compact_tokens": post_compact_tokens,
        "entry_skill": entry_skill,
        "last_ts": last_ts,
    }


def find_missed_runs(events: list[dict], min_run: int, threshold: int) -> list[dict]:
    """Maximal runs of consecutive turns with cache_read >= threshold,
    broken by any compact/clear event or below-threshold turn. Returns the
    runs of length >= min_run."""
    runs = []
    current: list[dict] = []
    start = 0
    for i, ev in enumerate(events):
        if ev["kind"] == "turn" and ev["cache_read"] >= threshold:
            if not current:
                start = i
            current.append(ev)
        else:
            if len(current) >= min_run:
                runs.append({"start": start, "length": len(current), "turns": current})
            current = []
    if len(current) >= min_run:
        runs.append({"start": start, "length": len(current), "turns": current})
    return runs


def run_recoverable_usd(turns: list[dict], median_post: int) -> float:
    """Counterfactual upper bound: compact at the run's first turn, then
    every later turn reads median_post instead of its actual cache_read."""
    usd = 0.0
    for t in turns[1:]:
        saved = max(0, t["cache_read"] - median_post)
        pricing = ts.resolve_pricing(t["model"])
        if pricing is None:
            continue
        usd += saved * pricing["cache_read"] / 1_000_000
    return usd


def audit_corpus(projects_dir: Path, days: int, min_run: int, threshold: int) -> dict:
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    trajectories = []
    files_seen = 0
    for project, session_id, agent_id, path in ts.iter_trace_files(projects_dir):
        files_seen += 1
        try:
            traj = parse_trajectory(path)
        except OSError as e:
            log.warning("unreadable %s: %s", path, e)
            continue
        if traj["last_ts"] is None or traj["last_ts"] < cutoff:
            continue
        trajectories.append((project, session_id, agent_id, traj))

    post_reads = [r for _, _, _, t in trajectories for r in t["post_compact_reads"]]
    post_tokens = [r for _, _, _, t in trajectories for r in t["post_compact_tokens"]]
    if post_reads:
        median_post, median_source = int(statistics.median(post_reads)), "next-turn cache_read"
    elif post_tokens:
        median_post, median_source = int(statistics.median(post_tokens)), "boundary postTokens"
    else:
        median_post, median_source = DEFAULT_POST_COMPACT_TOKENS, "default (no compactions)"

    run_rows = []
    compactions = clears = 0
    for project, session_id, agent_id, traj in trajectories:
        compactions += sum(1 for e in traj["events"] if e["kind"] == "compact")
        clears += sum(1 for e in traj["events"] if e["kind"] == "clear")
        for run in find_missed_runs(traj["events"], min_run, threshold):
            usd = run_recoverable_usd(run["turns"], median_post)
            reads = [t["cache_read"] for t in run["turns"]]
            run_rows.append(
                {
                    "project": project,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "entry_skill": traj["entry_skill"] or "",
                    "run_start_event": run["start"],
                    "run_turns": run["length"],
                    "mean_cache_read": sum(reads) // len(reads),
                    "max_cache_read": max(reads),
                    "recoverable_usd": round(usd, 4),
                }
            )

    def _agg(key):
        out = {}
        for r in run_rows:
            k = r[key] or "(none)"
            a = out.setdefault(k, {"runs": 0, "recoverable_usd": 0.0})
            a["runs"] += 1
            a["recoverable_usd"] += r["recoverable_usd"]
        return {
            k: {"runs": v["runs"], "recoverable_usd": round(v["recoverable_usd"], 2)}
            for k, v in sorted(out.items(), key=lambda kv: -kv[1]["recoverable_usd"])
        }

    sessions = {}
    for r in run_rows:
        key = (r["project"], r["session_id"])
        s = sessions.setdefault(
            key,
            {
                "project": r["project"],
                "session_id": r["session_id"],
                "entry_skill": r["entry_skill"],
                "runs": 0,
                "recoverable_usd": 0.0,
            },
        )
        s["runs"] += 1
        s["recoverable_usd"] += r["recoverable_usd"]
    top_sessions = sorted(sessions.values(), key=lambda s: -s["recoverable_usd"])[:20]
    for s in top_sessions:
        s["recoverable_usd"] = round(s["recoverable_usd"], 2)

    return {
        "window_days": days,
        "min_run": min_run,
        "threshold_tokens": threshold,
        "files_seen": files_seen,
        "agents_in_window": len(trajectories),
        "compactions_observed": compactions,
        "clears_observed": clears,
        "post_compact_median_tokens": median_post,
        "post_compact_median_source": median_source,
        "missed_runs": len(run_rows),
        "recoverable_usd_upper_bound": round(sum(r["recoverable_usd"] for r in run_rows), 2),
        "by_project": _agg("project"),
        "by_entry_skill": _agg("entry_skill"),
        "top_sessions": top_sessions,
        "run_rows": run_rows,
    }


CSV_COLUMNS = [
    "project",
    "session_id",
    "agent_id",
    "entry_skill",
    "run_start_event",
    "run_turns",
    "mean_cache_read",
    "max_cache_read",
    "recoverable_usd",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect missed compact/clear opportunities in session traces."
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path("~/.claude/projects").expanduser(),
        help="Root of the trace corpus (default: ~/.claude/projects)",
    )
    parser.add_argument("--days", type=int, default=28, help="Window in days (default 28)")
    parser.add_argument(
        "--min-run",
        type=int,
        default=30,
        help="Minimum consecutive high-context turns to flag (default 30)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=300_000,
        help="Per-turn cache_read floor in tokens (default 300000)",
    )
    parser.add_argument("--output", type=Path, help="Write per-run rows to this CSV")
    parser.add_argument(
        "--json", action="store_true", help="Print the summary as JSON to stdout"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    summary = audit_corpus(args.projects_dir, args.days, args.min_run, args.threshold)
    run_rows = summary.pop("run_rows")

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(run_rows)
        log.info("wrote %d runs to %s", len(run_rows), args.output)

    if args.json:
        json.dump(summary, sys.stdout, indent=2, default=str)
        print()
    else:
        log.info(
            "agents=%d missed_runs=%d recoverable<=$%s (median_post=%d from %s)",
            summary["agents_in_window"],
            summary["missed_runs"],
            summary["recoverable_usd_upper_bound"],
            summary["post_compact_median_tokens"],
            summary["post_compact_median_source"],
        )


if __name__ == "__main__":
    main()
