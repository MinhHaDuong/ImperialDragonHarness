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

Context length is the whole prompt of a turn: input, cache-read and
cache-creation tokens (ticket 1499; `--metric cache_read` gives the June audit's
older quantity). Besides runs, the audit counts main sessions: how many reached
each level, and how many went past the ceiling of their own main model, read
from skills/route/ceilings.json. Events are restricted to the window turn by
turn. A transcript it cannot read is counted and reported, never read as zero.

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

# A real /clear record pairs the two tags across an actual newline; trace
# text *quoted* inside a session (e.g. trace-doctor work) keeps the JSON
# escape as literal backslash-n and so does not match.
CLEAR_RE = re.compile(
    r"<command-name>/?clear</command-name>\s*\n\s*<command-message>clear</command-message>"
)

# Used only if the corpus contains no compaction to take a median from.
DEFAULT_POST_COMPACT_TOKENS = 20_000

CEILINGS_PATH = Path(__file__).resolve().parent.parent / "skills" / "route" / "ceilings.json"
METRICS = ("prompt", "cache_read")
METRIC_LABEL = {
    "prompt": "whole prompt (input + cache read + cache creation)",
    "cache_read": "cache_read tokens only",
}
# The levels of the design note's table, and its session floors.
LEVELS = (230_000, 450_000, 550_000)
MIN_TURNS_AT_LEVEL = 30
LONG_SESSION_TURNS = 100


class CouldNotLook(Exception):
    """The corpus cannot be read at all: not an empty result."""


def load_ceilings(path: Path = CEILINGS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ceiling_for(model: str, ceilings: dict) -> int:
    """Interface-session ceiling of a model id: the first entry that shares a
    whole word with it, else the default."""
    words = set(re.split(r"[-._/:\s]+", (model or "").lower()))
    for entry in ceilings.get("interface_session", []):
        if words & {m.lower() for m in entry["models"]}:
            return int(entry["tokens"])
    return int(ceilings["default_tokens"])


def _ctx(ev: dict, metric: str = "prompt") -> int:
    if metric == "prompt" and "prompt" in ev:
        return ev["prompt"]
    return ev["cache_read"]


def _fmt_k(n: int) -> str:
    return f"{n // 1000}K"


def _user_text_parts(content) -> list[str]:
    """Text of a user record: plain string, or the text blocks of list-form
    content (tool_result blocks carry no commands and are skipped)."""
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [
            b["text"]
            for b in content
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
        ]
    return []


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
    first_ts = None
    unparsable = 0

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                unparsable += 1
                continue
            if not isinstance(rec, dict):
                unparsable += 1
                continue

            tstamp = ts._parse_ts(rec.get("timestamp", ""))
            if tstamp is not None:
                last_ts = tstamp
                if first_ts is None:
                    first_ts = tstamp

            rec_type = rec.get("type")
            if rec_type == "system" and rec.get("subtype") == "compact_boundary":
                events.append({"kind": "compact", "ts": tstamp})
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
                    prompt = (
                        (usage.get("input_tokens", 0) or 0)
                        + cache_read
                        + (usage.get("cache_creation_input_tokens", 0) or 0)
                    )
                    events.append(
                        {
                            "kind": "turn",
                            "cache_read": cache_read,
                            "prompt": prompt,
                            "model": model,
                            "msg_id": msg_id,
                            "ts": tstamp,
                        }
                    )
                    if awaiting_post_read:
                        post_compact_reads.append(cache_read)
                        awaiting_post_read = False
            elif rec_type == "user":
                for text in _user_text_parts(content):
                    if CLEAR_RE.search(text):
                        events.append({"kind": "clear", "ts": tstamp})
                    elif entry_skill is None:
                        for m in re.finditer(
                            r"<command-name>/?([\w-]+)</command-name>", text
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
        "first_ts": first_ts,
        "unparsable_lines": unparsable,
    }


def drop_inherited_turns(trajectories: list[tuple]) -> int:
    """Strip turns a trajectory inherited from an earlier one, corpus-wide.

    `parse_trajectory` dedups turns by message id within a single file. A fork
    or resume starts a NEW file that replays the parent's records verbatim —
    same message ids — so the per-file set never sees them and every inherited
    turn is counted a second time. On the 2026-07-27 census that inflated the
    recoverable-compaction figure by ~28% ($278.68 -> ~$201): two session pairs
    contributed byte-identical runs.

    Trajectories are processed oldest-first so the originating session keeps its
    turns and the fork contributes only what it actually added. Turns are
    dropped in place; compact/clear events are left alone, since a fork
    genuinely re-enters that state. Returns the number of turns dropped.
    """
    from datetime import datetime, timezone

    epoch = datetime.min.replace(tzinfo=timezone.utc)
    ordered = sorted(
        trajectories,
        key=lambda item: (item[3]["first_ts"] or epoch, item[1], item[2]),
    )
    claimed: set[str] = set()
    dropped = 0
    for _, _, _, traj in ordered:
        kept = []
        for ev in traj["events"]:
            if ev["kind"] == "turn":
                mid = ev.get("msg_id")
                if mid is not None:
                    if mid in claimed:
                        dropped += 1
                        continue
                    claimed.add(mid)
            kept.append(ev)
        traj["events"] = kept
    return dropped


def find_missed_runs(
    events: list[dict], min_run: int, threshold: int, metric: str = "prompt"
) -> list[dict]:
    """Maximal runs of consecutive turns with context >= threshold,
    broken by any compact/clear event or below-threshold turn. Returns the
    runs of length >= min_run."""
    runs = []
    current: list[dict] = []
    start = 0
    for i, ev in enumerate(events):
        if ev["kind"] == "turn" and _ctx(ev, metric) >= threshold:
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


def window_start(now, days: int, since: str | None):
    """Start of the window: `since` (YYYY-MM-DD, UTC midnight) or `days` before now."""
    from datetime import datetime, timedelta, timezone

    if since:
        return datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
    return now - timedelta(days=days)


def restrict_to_window(events: list[dict], start) -> tuple[list[dict], int]:
    """Events stamped at or after `start`; an unstamped event cannot be placed
    and is dropped, counted in the second value."""
    kept, undated = [], 0
    for ev in events:
        if ev.get("ts") is None:
            undated += 1
        elif ev["ts"] >= start:
            kept.append(ev)
    return kept, undated


def main_model(events: list[dict]) -> str:
    """The model that served most turns of a trajectory."""
    counts: dict[str, int] = {}
    for ev in events:
        if ev["kind"] == "turn":
            counts[ev["model"]] = counts.get(ev["model"], 0) + 1
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0] if counts else ""


def session_report(main_trajs: list[tuple], ceilings: dict, metric: str, levels=LEVELS) -> dict:
    """Counts over main sessions, one row per session however many runs it had."""
    rows = []
    for project, session_id, traj in main_trajs:
        turns = [e for e in traj["events"] if e["kind"] == "turn"]
        if not turns:
            continue
        model = main_model(traj["events"])
        ceiling = ceiling_for(model, ceilings)
        ctx = [_ctx(t, metric) for t in turns]
        rows.append(
            {
                "project": project,
                "session_id": session_id,
                "main_model": model,
                "turns": len(turns),
                "peak": max(ctx),
                "ceiling": ceiling,
                "turns_over_ceiling": sum(1 for c in ctx if c >= ceiling),
                "at_level": {str(lv): sum(1 for c in ctx if c >= lv) for lv in levels},
            }
        )

    def by_model(selected):
        out: dict[str, int] = {}
        for r in selected:
            out[r["main_model"]] = out.get(r["main_model"], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    level_rows = {}
    for lv in levels:
        sel = [r for r in rows if r["at_level"][str(lv)] >= MIN_TURNS_AT_LEVEL]
        level_rows[str(lv)] = {"sessions": len(sel), "by_model": by_model(sel)}
    over = [r for r in rows if r["turns_over_ceiling"] >= MIN_TURNS_AT_LEVEL]
    over.sort(key=lambda r: -r["peak"])
    return {
        "metric": metric,
        "metric_label": METRIC_LABEL[metric],
        "with_turns": len(rows),
        "turns_in_window": sum(r["turns"] for r in rows),
        "long_sessions": sum(1 for r in rows if r["turns"] >= LONG_SESSION_TURNS),
        "min_turns_at_level": MIN_TURNS_AT_LEVEL,
        "levels": level_rows,
        "over_own_ceiling": {
            "sessions": len(over),
            "by_model": by_model(over),
            "rows": [{k: v for k, v in r.items() if k != "at_level"} for r in over[:20]],
        },
    }


def audit_corpus(
    projects_dir: Path,
    days: int,
    min_run: int,
    threshold: int | None = None,
    *,
    since: str | None = None,
    now=None,
    ceilings: dict | None = None,
    metric: str = "prompt",
) -> dict:
    """Audit the corpus. `threshold` None means each agent's own: its main
    model's ceiling for a main session, the default (230K) for a subagent."""
    from datetime import datetime, timezone

    if not Path(projects_dir).is_dir():
        raise CouldNotLook(f"no trace corpus at {projects_dir}")
    now = now or datetime.now(timezone.utc)
    ceilings = ceilings or load_ceilings()
    start = window_start(now, days, since)

    trajectories = []
    files_seen = unreadable = unparsable = 0
    for project, session_id, agent_id, path in ts.iter_trace_files(projects_dir):
        files_seen += 1
        try:
            traj = parse_trajectory(path)
        except OSError as e:
            log.warning("could not look at %s: %s", path, e)
            unreadable += 1
            continue
        unparsable += traj["unparsable_lines"]
        trajectories.append((project, session_id, agent_id, traj))

    # Inherited turns are dropped on whole transcripts, before the window cut.
    duplicate_turns = drop_inherited_turns(trajectories)
    if duplicate_turns:
        log.info(
            "dropped %d turns inherited by forked/resumed sessions", duplicate_turns
        )

    undated = 0
    in_window = []
    for item in trajectories:
        item[3]["events"], n = restrict_to_window(item[3]["events"], start)
        undated += n
        if item[3]["events"]:
            in_window.append(item)
    trajectories = in_window

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
        model = main_model(traj["events"])
        if threshold is not None:
            agent_threshold = threshold
        elif agent_id == "main":
            agent_threshold = ceiling_for(model, ceilings)
        else:
            agent_threshold = int(ceilings["default_tokens"])
        for run in find_missed_runs(traj["events"], min_run, agent_threshold, metric):
            usd = run_recoverable_usd(run["turns"], median_post)
            reads = [_ctx(t, metric) for t in run["turns"]]
            run_rows.append(
                {
                    "project": project,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "main_model": model,
                    "threshold": agent_threshold,
                    "entry_skill": traj["entry_skill"] or "",
                    "run_start_event": run["start"],
                    "run_turns": run["length"],
                    "mean_context": sum(reads) // len(reads),
                    "max_context": max(reads),
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

    main_trajs = [(p, sid, t) for p, sid, aid, t in trajectories if aid == "main"]

    return {
        "window_days": days,
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "min_run": min_run,
        "threshold_tokens": threshold if threshold is not None else "per model (skills/route/ceilings.json)",
        "metric": metric,
        "files_seen": files_seen,
        "unreadable_files": unreadable,
        "unparsable_lines": unparsable,
        "undated_events_dropped": undated,
        "agents_in_window": len(trajectories),
        "inherited_turns_dropped": duplicate_turns,
        "compactions_observed": compactions,
        "clears_observed": clears,
        "post_compact_median_tokens": median_post,
        "post_compact_median_source": median_source,
        "missed_runs": len(run_rows),
        "sessions_with_missed_runs": len(sessions),
        "recoverable_usd_upper_bound": round(sum(r["recoverable_usd"] for r in run_rows), 2),
        "by_project": _agg("project"),
        "by_entry_skill": _agg("entry_skill"),
        "top_sessions": top_sessions,
        "sessions": session_report(main_trajs, ceilings, metric),
        "run_rows": run_rows,
    }


def render_table(summary: dict) -> str:
    """The design note's section 1 table, as text."""
    sr = summary["sessions"]
    n = sr["min_turns_at_level"]
    lines = [
        f"Context length audit, main sessions, {summary['window_start'][:10]} to {summary['window_end'][:10]}",
        f"Context length counted as: {sr['metric_label']}",
        f"sessions with at least one turn: {sr['with_turns']}",
        f"sessions with {LONG_SESSION_TURNS} or more turns: {sr['long_sessions']}",
    ]
    for lv, row in sr["levels"].items():
        models = ", ".join(f"{c} on {m or '(unknown)'}" for m, c in row["by_model"].items())
        lines.append(
            f"sessions with {n} or more turns at or above {_fmt_k(int(lv))}: {row['sessions']}"
            + (f" ({models})" if models else "")
        )
    over = sr["over_own_ceiling"]
    models = ", ".join(f"{c} on {m or '(unknown)'}" for m, c in over["by_model"].items())
    lines.append(
        f"sessions with {n} or more turns past the ceiling of their main model: {over['sessions']}"
        + (f" ({models})" if models else "")
    )
    lines.append(
        "A main session is not known to be an interface session: the ceiling is the model's, "
        "an unattended run is bound by the default."
    )
    lines.append(
        f"missed runs: {summary['missed_runs']} in {summary['sessions_with_missed_runs']} sessions"
    )
    if summary["unreadable_files"]:
        lines.append(
            f"COULD NOT LOOK at {summary['unreadable_files']} of {summary['files_seen']} "
            "transcripts: the counts above leave them out"
        )
    if summary["unparsable_lines"]:
        lines.append(f"{summary['unparsable_lines']} transcript lines could not be parsed")
    return "\n".join(lines)


CSV_COLUMNS = [
    "project",
    "session_id",
    "agent_id",
    "main_model",
    "threshold",
    "entry_skill",
    "run_start_event",
    "run_turns",
    "mean_context",
    "max_context",
    "recoverable_usd",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Which sessions overran their context ceiling, and what missed "
        "compact/clear runs cost. Context length is the whole prompt per turn "
        "(input + cache read + cache creation) unless --metric says otherwise."
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path("~/.claude/projects").expanduser(),
        help="Root of the trace corpus (default: ~/.claude/projects)",
    )
    parser.add_argument("--days", type=int, default=28, help="Window in days (default 28)")
    parser.add_argument(
        "--since",
        help="Window start as YYYY-MM-DD (UTC), instead of --days; the design note's table uses 2026-11-01",
    )
    parser.add_argument(
        "--min-run",
        type=int,
        default=30,
        help="Minimum consecutive high-context turns to flag (default 30)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Per-turn context floor in tokens for every agent "
        "(default: each main model's ceiling from skills/route/ceilings.json, 230000 for subagents)",
    )
    parser.add_argument(
        "--metric",
        choices=METRICS,
        default="prompt",
        help="prompt: input + cache read + cache creation (default); "
        "cache_read: the June 2026 audit's quantity",
    )
    parser.add_argument("--output", type=Path, help="Write per-run rows to this CSV")
    parser.add_argument(
        "--json", action="store_true", help="Print the summary as JSON to stdout"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        summary = audit_corpus(
            args.projects_dir,
            args.days,
            args.min_run,
            args.threshold,
            since=args.since,
            metric=args.metric,
        )
    except (CouldNotLook, OSError, ValueError) as e:
        print(f"could not look: {e}", file=sys.stderr)
        return 2
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
        print(render_table(summary))
        log.info(
            "agents=%d missed_runs=%d recoverable<=$%s (median_post=%d from %s)",
            summary["agents_in_window"],
            summary["missed_runs"],
            summary["recoverable_usd_upper_bound"],
            summary["post_compact_median_tokens"],
            summary["post_compact_median_source"],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
