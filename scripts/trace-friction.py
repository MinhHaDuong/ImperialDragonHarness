#!/usr/bin/env python3
"""Trace-friction scan (ticket 1169): velocity losses in Claude Code transcripts.

Zero-LLM, standard-library-only companion to trace-stats.py: that measures
cost, this measures friction. Method: docs/2026-10-21-velocity-friction-scan.md.

Walks ~/.claude/projects (main sessions and subagents), pairs each tool_use
with its tool_result, and reports per day:

* tool calls and tool errors, errors split by cause (worktree-guard refusal,
  "No such tool available", Write-outside-worktree, other);
* calls slower than 30 s, by tool;
* Bash commands matching the wait regex.

The series is DAILY on purpose: period totals hid that guard refusals stopped
on 2026-10-15. Totals are derived from the series.

Limits, stated in the output as well: a duration is tool_use timestamp to
tool_result timestamp, so it includes permission waits and background
commands, an UPPER BOUND on tool wall-clock. The wait regex still over-counts
when the keyword sits inside quoted text or a heredoc. Cause classes are
message-text heuristics; "other" is the residual.
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("trace-friction")

SLOW_SECONDS = 30.0
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
CAUSES = ("worktree_guard", "no_such_tool", "write_outside_worktree", "other")

NO_SUCH_TOOL_RE = re.compile(r"No such tool available")
GUARD_RE = re.compile(
    r"too complex to verify|shared[ -]checkout|Edit the worktree copy"
    r"|PreToolUse:[\w|]* ?hook error|worktree[- ](?:path )?(?:guard|isolation)"
    r"|resolves to the main repo|hasn't isolated its changes"
    r"|isolated in the worktree",
    re.IGNORECASE,
)
OUTSIDE_RE = re.compile(
    r"outside the (?:current |assigned )?worktree|Edit the worktree copy"
    r"|resolves to the main repo|hasn't isolated its changes|Call EnterWorktree first"
    r"|writes are limited to",
    re.IGNORECASE,
)
# Tightened wait regex: a numeric sleep, a watch flag or subcommand, or an
# `until` loop at command position, or after `do`/`then`/`else`/`timeout N`.
# Quoted or heredoc text can still match.
WAIT_RE = re.compile(
    r"(?:^|[;&|(]\s*|\n\s*|\b(?:do|then|else)\s+|\btimeout\s+\d+\w*\s+)"
    r"(?:sleep\s+\d|until\s)"
    r"|--watch\b|\bgh\s+(?:run|pr\s+checks)\s+watch\b"
)


def classify_error(tool: str, text: str) -> str:
    """Return the cause class of one errored tool_result."""
    if NO_SUCH_TOOL_RE.search(text):
        return "no_such_tool"
    if tool in WRITE_TOOLS and OUTSIDE_RE.search(text):
        return "write_outside_worktree"
    if GUARD_RE.search(text):
        return "worktree_guard"
    return "other"


def is_wait_command(command: str) -> bool:
    return bool(WAIT_RE.search(command))


def _parse_ts(s) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def iter_trace_files(projects_dir: Path, cutoff_ts: float):
    """Yield trace paths modified since cutoff; tolerate dangling symlinks."""
    patterns = ("*/*.jsonl", "*/*/subagents/agent-*.jsonl")
    for pattern in patterns:
        for path in sorted(projects_dir.glob(pattern)):
            try:
                if os.path.getmtime(path) < cutoff_ts:
                    continue
            except OSError as e:  # dangling symlink, vanished file
                log.warning("skipping %s: %s", path, e)
                continue
            yield path


def new_day() -> dict:
    return {
        "calls": 0,
        "bash_calls": 0,
        "errors": 0,
        "errors_by_cause": {c: 0 for c in CAUSES},
        "slow_calls": 0,
        "slow_seconds": 0.0,
        "slow_by_tool": {},
        "wait_commands": 0,
        "wait_seconds": 0.0,
        "error_seconds": 0.0,
    }


def scan_file(path: Path, cutoff: datetime, seen: set, days: dict) -> int:
    """Fold one transcript into the per-day table; return skipped line count."""
    pending: dict[str, tuple[datetime, str, str]] = {}
    skipped = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                skipped += 1
                continue
            msg = row.get("message") if isinstance(row, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            ts = _parse_ts(row.get("timestamp"))
            if not isinstance(content, list) or ts is None:
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                kind = block.get("type")
                tid = (
                    block.get("id") if kind == "tool_use" else block.get("tool_use_id")
                )
                if not isinstance(tid, str):
                    continue
                if kind == "tool_use":
                    inp = block.get("input")
                    cmd = inp.get("command", "") if isinstance(inp, dict) else ""
                    pending[tid] = (ts, str(block.get("name", "?")), str(cmd))
                elif kind == "tool_result" and tid in pending:
                    start, tool, cmd = pending.pop(tid)
                    if tid in seen or start < cutoff:
                        continue  # resumed sessions replay parent rows
                    seen.add(tid)
                    _record(days, start, ts, tool, cmd, block)
    return skipped


def _record(days: dict, start, end, tool: str, cmd: str, block: dict) -> None:
    day = days[start.date().isoformat()]
    secs = max((end - start).total_seconds(), 0.0)
    day["calls"] += 1
    if tool == "Bash":
        day["bash_calls"] += 1
        if is_wait_command(cmd):
            day["wait_commands"] += 1
            day["wait_seconds"] += secs
    if block.get("is_error"):
        cause = classify_error(tool, _result_text(block.get("content")))
        day["errors"] += 1
        day["errors_by_cause"][cause] += 1
        day["error_seconds"] += secs
    if secs > SLOW_SECONDS:
        day["slow_calls"] += 1
        day["slow_seconds"] += secs
        entry = day["slow_by_tool"].setdefault(tool, {"calls": 0, "seconds": 0.0})
        entry["calls"] += 1
        entry["seconds"] += secs


def run_scan(projects_dir: Path, days: int, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    table: dict[str, dict] = defaultdict(new_day)
    seen: set = set()
    files = skipped = 0
    for path in iter_trace_files(projects_dir, cutoff.timestamp()):
        try:
            skipped += scan_file(path, cutoff, seen, table)
        except OSError as e:
            log.warning("unreadable %s: %s", path, e)
            continue
        files += 1
    series = [{"date": d, **table[d]} for d in sorted(table)]
    return summarize(series, days, files, skipped)


def summarize(series: list[dict], days: int, files: int, skipped: int) -> dict:
    causes: Counter = Counter()
    tail: dict[str, dict] = {}
    for d in series:
        causes.update(d["errors_by_cause"])
        for tool, e in d["slow_by_tool"].items():
            t = tail.setdefault(tool, {"calls": 0, "seconds": 0.0})
            t["calls"] += e["calls"]
            t["seconds"] += e["seconds"]
    calls = sum(d["calls"] for d in series)
    errors = sum(d["errors"] for d in series)
    return {
        "window_days": days,
        "files": files,
        "skipped_lines": skipped,
        "duration_note": (
            "durations are tool_use to tool_result: an upper bound, they include "
            "permission waits and background commands"
        ),
        "wait_note": "wait regex tightened but still over-counts quoted or heredoc text",
        "totals": {
            "calls": calls,
            "bash_calls": sum(d["bash_calls"] for d in series),
            "errors": errors,
            "error_rate": round(errors / calls, 4) if calls else 0.0,
            "errors_by_cause": {c: causes.get(c, 0) for c in CAUSES},
            "error_hours_upper_bound": round(
                sum(d["error_seconds"] for d in series) / 3600, 2
            ),
            "slow_calls": sum(d["slow_calls"] for d in series),
            "slow_hours_upper_bound": round(
                sum(d["slow_seconds"] for d in series) / 3600, 2
            ),
            "wait_commands": sum(d["wait_commands"] for d in series),
            "wait_hours_upper_bound": round(
                sum(d["wait_seconds"] for d in series) / 3600, 2
            ),
        },
        "slow_by_tool_hours_upper_bound": [
            {"tool": t, "calls": e["calls"], "hours": round(e["seconds"] / 3600, 2)}
            for t, e in sorted(tail.items(), key=lambda kv: -kv[1]["seconds"])
        ],
        "daily": series,
    }


CSV_COLUMNS = [
    "date", "calls", "bash_calls", "errors", *CAUSES, "slow_calls",
    "slow_hours_ub", "wait_commands", "wait_hours_ub",
]  # fmt: skip


def write_csv(path: Path, summary: dict) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for d in summary["daily"]:
            writer.writerow(
                {
                    "date": d["date"],
                    "calls": d["calls"],
                    "bash_calls": d["bash_calls"],
                    "errors": d["errors"],
                    **d["errors_by_cause"],
                    "slow_calls": d["slow_calls"],
                    "slow_hours_ub": round(d["slow_seconds"] / 3600, 3),
                    "wait_commands": d["wait_commands"],
                    "wait_hours_ub": round(d["wait_seconds"] / 3600, 3),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Daily friction series from Claude Code traces."
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path("~/.claude/projects").expanduser(),
        help="Root of the trace corpus (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--days", type=int, default=28, help="Window in days (default 28)"
    )
    parser.add_argument(
        "--output", type=Path, help="Write the daily series to this CSV"
    )
    parser.add_argument("--json", action="store_true", help="Print the summary as JSON")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    summary = run_scan(args.projects_dir, args.days)
    if args.output:
        write_csv(args.output, summary)
        log.info("wrote %d days to %s", len(summary["daily"]), args.output)
    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        print()
        return
    print("date        calls  errors  guard  notool  wr-out  other  slow>30s  waits")
    for d in summary["daily"]:
        c = d["errors_by_cause"]
        print(
            f"{d['date']}  {d['calls']:5d}  {d['errors']:6d}  {c['worktree_guard']:5d}"
            f"  {c['no_such_tool']:6d}  {c['write_outside_worktree']:6d}  {c['other']:5d}"
            f"  {d['slow_calls']:8d}  {d['wait_commands']:5d}"
        )
    print(summary["duration_note"])


if __name__ == "__main__":
    main()
