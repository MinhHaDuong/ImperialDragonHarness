#!/usr/bin/env python3
"""Trace-stats census — deterministic, zero-LLM-token accounting of Claude Code session traces.

Walks ~/.claude/projects/, parses every main-session and subagent JSONL trace
in the window, and emits one CSV row per agent plus a session-level rollup.

CRITICAL accounting rule (ticket 0237 / 0236): one assistant message spans
multiple JSONL rows — one per content block — each repeating the same
`message.usage` object. Usage is counted ONCE per unique `message.id`
(summing per row overstates ~2.7x). `<synthetic>` model records are
harness-injected and carry no API cost: excluded from $ and token sums,
counted in `synthetic_messages`.

Emits JSON summary: {window, files, sessions, totals, skipped_lines, rollup}
"""

import argparse
import csv
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("trace-stats")

# $/MTok, per category. Source: claude-api skill pricing tables (2026-06).
# Cache read = 0.1x input; 5m cache write = 1.25x; 1h cache write = 2x.
PRICING = {
    "fable": {
        "input": 10.0,
        "output": 50.0,
        "cache_read": 1.0,
        "cache_write_5m": 12.5,
        "cache_write_1h": 20.0,
    },
    "opus": {
        "input": 5.0,
        "output": 25.0,
        "cache_read": 0.5,
        "cache_write_5m": 6.25,
        "cache_write_1h": 10.0,
    },
    "sonnet": {
        "input": 3.0,
        "output": 15.0,
        "cache_read": 0.3,
        "cache_write_5m": 3.75,
        "cache_write_1h": 6.0,
    },
    "haiku": {
        "input": 1.0,
        "output": 5.0,
        "cache_read": 0.1,
        "cache_write_5m": 1.25,
        "cache_write_1h": 2.0,
    },
}

WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}

# Built-in CLI commands that appear as <command-name> but are not entry skills.
BUILTIN_COMMANDS = {
    "clear",
    "compact",
    "model",
    "login",
    "logout",
    "resume",
    "exit",
    "help",
    "config",
    "cost",
    "doctor",
    "status",
    "context",
    "agents",
    "mcp",
    "memory",
    "todos",
    "rewind",
}

USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)

# Ticket 0243 (H11): a turn is "navigational" when every tool call on it
# matches this — pure orientation, no mutation, no new information source.
NAV_COMMAND_RE = re.compile(
    r"^\s*(?:cd|ls|pwd)\b|^\s*git\s+(?:status|log|branch|show-current)\b"
)

# Ticket 0243 (H10): delivery completed inside the session. Matched against
# JSON-encoded tool_result content; upper bound (quoted text also matches).
MERGE_MARKER_RE = re.compile(r"Merge queued|Pull Request successfully merged|state=MERGED")

# Ticket 0243 (H13): verification machinery re-entry.
VERIFY_SKILLS = {"verify", "gaze", "verify-gate"}

# Ticket 0244 (H10'): PR numbers cited in a merge-marker tool result.
PR_NUMBER_RE = re.compile(r"(?:PR\s*#|pulls/)(\d+)")

# Ticket 0244 (H10'): harness-mandated wrap-up work — memory/STATE writes,
# branch hygiene, wrap-up skills. Used only to classify tail turns.
MANDATED_PATH_RE = re.compile(r"/memory/|MEMORY\.md|STATE\.md")
MANDATED_BASH_RE = re.compile(r"^\s*git\s+(?:branch|worktree|fetch\s+--prune)|erg\s+close")
MANDATED_SKILLS = {"roar", "lair", "dream", "molt", "memory", "housekeeping"}
PATH_TOOLS = {"Read", "Edit", "Write", "NotebookEdit"}


def _is_nav_tool(name: str, tool_input: dict) -> bool:
    return name == "Bash" and bool(NAV_COMMAND_RE.search(str(tool_input.get("command", ""))))


def _is_mandated_tool(name: str, tool_input: dict) -> bool:
    if name in PATH_TOOLS:
        return bool(MANDATED_PATH_RE.search(str(tool_input.get("file_path", ""))))
    if name == "Bash":
        return bool(MANDATED_BASH_RE.search(str(tool_input.get("command", ""))))
    if name == "Skill":
        return tool_input.get("skill") in MANDATED_SKILLS
    return False


def resolve_pricing(model_id: str) -> dict | None:
    """Map a model id to its pricing family; None for unknown models."""
    for family in ("fable", "opus", "sonnet", "haiku"):
        if family in model_id:
            return PRICING[family]
    return None


def strip_worktree(project_dir_name: str) -> str:
    """Strip the worktree suffix from an encoded project dir name."""
    return re.sub(r"--claude-worktrees-.+$", "", project_dir_name)


def _parse_ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _message_cost(model: str, usage: dict) -> float:
    p = resolve_pricing(model)
    if p is None:
        return 0.0
    cache_creation = usage.get("cache_creation") or {}
    total_write = usage.get("cache_creation_input_tokens", 0) or 0
    write_1h = cache_creation.get("ephemeral_1h_input_tokens", 0) or 0
    write_5m = cache_creation.get("ephemeral_5m_input_tokens")
    if write_5m is None:
        # No 5m key: whatever the 1h bucket doesn't account for was 5m.
        write_5m = max(0, total_write - write_1h)
    dollars = (
        (usage.get("input_tokens", 0) or 0) * p["input"]
        + (usage.get("output_tokens", 0) or 0) * p["output"]
        + (usage.get("cache_read_input_tokens", 0) or 0) * p["cache_read"]
        + (write_5m or 0) * p["cache_write_5m"]
        + (write_1h or 0) * p["cache_write_1h"]
    )
    return dollars / 1_000_000


def parse_trace_file(path: Path) -> dict:
    """Parse one trace JSONL file into per-agent statistics.

    Tolerant of malformed lines and records missing `message`/`usage`:
    those are counted (`skipped_lines`) or silently passed over, never fatal.
    """
    seen_ids: set[str] = set()
    seen_tool_use_ids: set[str] = set()
    tokens = dict.fromkeys(USAGE_KEYS, 0)
    cost = 0.0
    synthetic = 0
    unknown_model = 0
    skipped = 0
    total_lines = 0
    models: Counter = Counter()
    tool_counts: Counter = Counter()
    read_paths: Counter = Counter()
    bash_commands: Counter = Counter()
    ask_user = 0
    tool_result_bytes = 0
    wrote_files = False
    first_ts = last_ts = None
    final_cache_read = 0
    entry_skill = None
    turn_tool_kinds: list[list[str]] = []  # per non-synthetic turn: "nav"/"work" per tool
    msg_turn_index: dict[str, int] = {}
    merge_marker_turn: int | None = None
    verify_gaze = 0
    turn_cache_read: list[int] = []  # per non-synthetic turn, parallel to turn_tool_kinds
    turn_mandated: list[bool] = []
    merge_marker_turns: list[int] = []
    pr_numbers: list[int] = []
    vg_turns: list[int] = []  # 0-based turn index of each verify/gaze invocation
    first_turn_cache_write = 0

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total_lines += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(rec, dict):
                skipped += 1
                continue

            ts = _parse_ts(rec.get("timestamp", ""))
            if ts is not None:
                first_ts = first_ts or ts
                last_ts = ts

            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            rec_type = rec.get("type")
            content = msg.get("content")

            if rec_type == "assistant":
                model = msg.get("model") or ""
                msg_id = msg.get("id")
                usage = msg.get("usage")
                if msg_id and msg_id not in seen_ids and isinstance(usage, dict):
                    seen_ids.add(msg_id)
                    if model == "<synthetic>":
                        synthetic += 1
                    else:
                        if not turn_tool_kinds:
                            first_turn_cache_write = (
                                usage.get("cache_creation_input_tokens", 0) or 0
                            )
                        msg_turn_index[msg_id] = len(turn_tool_kinds)
                        turn_tool_kinds.append([])
                        turn_cache_read.append(usage.get("cache_read_input_tokens", 0) or 0)
                        turn_mandated.append(False)
                        models[model] += 1
                        for k in USAGE_KEYS:
                            tokens[k] += usage.get(k, 0) or 0
                        if resolve_pricing(model) is None:
                            unknown_model += 1
                        else:
                            cost += _message_cost(model, usage)
                        final_cache_read = usage.get("cache_read_input_tokens", 0) or 0
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        block_id = block.get("id")
                        if block_id and block_id in seen_tool_use_ids:
                            continue
                        if block_id:
                            seen_tool_use_ids.add(block_id)
                        name = block.get("name", "?")
                        tool_counts[name] += 1
                        tool_input = block.get("input") or {}
                        turn_idx = msg_turn_index.get(msg.get("id") or "")
                        if turn_idx is not None:
                            turn_tool_kinds[turn_idx].append(
                                "nav" if _is_nav_tool(name, tool_input) else "work"
                            )
                            if _is_mandated_tool(name, tool_input):
                                turn_mandated[turn_idx] = True
                        if name == "Skill" and tool_input.get("skill") in VERIFY_SKILLS:
                            verify_gaze += 1
                            if turn_idx is not None:
                                vg_turns.append(turn_idx)
                        if name in WRITE_TOOLS:
                            wrote_files = True
                        elif name == "Read" and tool_input.get("file_path"):
                            read_paths[tool_input["file_path"]] += 1
                        elif name == "Bash" and tool_input.get("command"):
                            bash_commands[tool_input["command"]] += 1
                        elif name == "AskUserQuestion":
                            ask_user += 1
                        elif name == "Skill" and entry_skill is None:
                            entry_skill = tool_input.get("skill")
            elif rec_type == "user":
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            try:
                                result_text = json.dumps(block.get("content", ""))
                            except (TypeError, ValueError):
                                continue
                            tool_result_bytes += len(result_text)
                            if MERGE_MARKER_RE.search(result_text):
                                if merge_marker_turn is None:
                                    merge_marker_turn = len(turn_tool_kinds)
                                merge_marker_turns.append(len(turn_tool_kinds))
                                for m in PR_NUMBER_RE.finditer(result_text):
                                    n = int(m.group(1))
                                    if n not in pr_numbers:
                                        pr_numbers.append(n)
                elif isinstance(content, str) and entry_skill is None:
                    for m in re.finditer(r"<command-name>/?([\w-]+)</command-name>", content):
                        if m.group(1) not in BUILTIN_COMMANDS:
                            entry_skill = m.group(1)
                            break

    nav_flags = [bool(kinds) and all(k == "nav" for k in kinds) for kinds in turn_tool_kinds]
    max_nav_run = run = 0
    for flag in nav_flags:
        run = run + 1 if flag else 0
        max_nav_run = max(max_nav_run, run)

    # Ticket 0244: disjoint per-turn cache_read buckets, priority
    # tail (after LAST merge marker) > vg (after 2nd verify/gaze) >
    # micro (nav/idle, never the final turn) > core. Turn numbers are
    # 1-based to match the marker convention (marker value = turns
    # completed when it arrived).
    n_turns = len(turn_tool_kinds)
    last_marker = merge_marker_turns[-1] if merge_marker_turns else None
    vg_second = vg_turns[1] + 1 if len(vg_turns) >= 2 else None
    bucket_tail_cr = bucket_vg_cr = bucket_micro_cr = 0
    tail_turn_count = tail_mandated = 0
    for i in range(n_turns):
        number = i + 1
        cr = turn_cache_read[i]
        if last_marker is not None and number > last_marker:
            bucket_tail_cr += cr
            tail_turn_count += 1
            if turn_mandated[i]:
                tail_mandated += 1
        elif vg_second is not None and number > vg_second:
            bucket_vg_cr += cr
        elif (nav_flags[i] or not turn_tool_kinds[i]) and i != n_turns - 1:
            bucket_micro_cr += cr

    return {
        **tokens,
        "cost_usd": cost,
        "turns": len(seen_ids) - synthetic,
        "nav_turns": sum(nav_flags),
        "idle_turns": sum(1 for kinds in turn_tool_kinds if not kinds),
        "max_nav_run": max_nav_run,
        "merge_marker_turn": merge_marker_turn,
        "verify_gaze_skills": verify_gaze,
        "merge_markers": len(merge_marker_turns),
        "merge_marker_turn_last": last_marker,
        "tail_turns": tail_turn_count,
        "tail_mandated_turns": tail_mandated,
        "bucket_tail_cr": bucket_tail_cr,
        "bucket_vg_cr": bucket_vg_cr,
        "bucket_micro_cr": bucket_micro_cr,
        "vg_second_turn": vg_second,
        "first_turn_cache_write": first_turn_cache_write,
        "excess_file_reads": sum(max(0, c - 1) for c in read_paths.values()),
        "pr_numbers": pr_numbers,
        "synthetic_messages": synthetic,
        "unknown_model_messages": unknown_model,
        "skipped_lines": skipped,
        "total_lines": total_lines,
        "models": models,
        "tool_counts": tool_counts,
        "tool_result_bytes": tool_result_bytes,
        "max_read_repeat": max(read_paths.values(), default=0),
        "max_bash_repeat": max(bash_commands.values(), default=0),
        "read_only": not wrote_files,
        "ask_user_questions": ask_user,
        "final_cache_read": final_cache_read,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "entry_skill": entry_skill,
    }


def iter_trace_files(projects_dir: Path):
    """Yield (project, session_id, agent_id, path) for every trace file."""
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir():
            continue
        project = strip_worktree(proj_dir.name)
        for main in sorted(proj_dir.glob("*.jsonl")):
            yield project, main.stem, "main", main
        for sub in sorted(proj_dir.glob("*/subagents/agent-*.jsonl")):
            yield project, sub.parent.parent.name, sub.stem, sub


CSV_COLUMNS = [
    "project",
    "session_id",
    "agent_id",
    "date",
    "model",
    "turns",
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "cost_usd",
    "synthetic_messages",
    "unknown_model_messages",
    "skipped_lines",
    "total_lines",
    "tool_histogram",
    "tool_result_bytes",
    "max_read_repeat",
    "max_bash_repeat",
    "read_only",
    "ask_user_questions",
    "final_cache_read",
    "nav_turns",
    "idle_turns",
    "max_nav_run",
    "merge_marker_turn",
    "verify_gaze_skills",
    "merge_markers",
    "merge_marker_turn_last",
    "tail_turns",
    "tail_mandated_turns",
    "bucket_tail_cr",
    "bucket_vg_cr",
    "bucket_micro_cr",
    "vg_second_turn",
    "first_turn_cache_write",
    "excess_file_reads",
    "pr_numbers",
    "entry_skill",
    "path",
]


def build_row(project: str, session_id: str, agent_id: str, path: Path, stats: dict) -> dict:
    dominant_model = stats["models"].most_common(1)
    return {
        "project": project,
        "session_id": session_id,
        "agent_id": agent_id,
        "date": stats["first_ts"].date().isoformat() if stats["first_ts"] else "",
        "model": dominant_model[0][0] if dominant_model else "",
        "turns": stats["turns"],
        "input_tokens": stats["input_tokens"],
        "output_tokens": stats["output_tokens"],
        "cache_read_input_tokens": stats["cache_read_input_tokens"],
        "cache_creation_input_tokens": stats["cache_creation_input_tokens"],
        "cost_usd": round(stats["cost_usd"], 4),
        "synthetic_messages": stats["synthetic_messages"],
        "unknown_model_messages": stats["unknown_model_messages"],
        "skipped_lines": stats["skipped_lines"],
        "total_lines": stats["total_lines"],
        "tool_histogram": json.dumps(dict(stats["tool_counts"]), sort_keys=True),
        "tool_result_bytes": stats["tool_result_bytes"],
        "max_read_repeat": stats["max_read_repeat"],
        "max_bash_repeat": stats["max_bash_repeat"],
        "read_only": stats["read_only"],
        "ask_user_questions": stats["ask_user_questions"],
        "final_cache_read": stats["final_cache_read"],
        "nav_turns": stats["nav_turns"],
        "idle_turns": stats["idle_turns"],
        "max_nav_run": stats["max_nav_run"],
        "merge_marker_turn": (
            "" if stats["merge_marker_turn"] is None else stats["merge_marker_turn"]
        ),
        "verify_gaze_skills": stats["verify_gaze_skills"],
        "merge_markers": stats["merge_markers"],
        "merge_marker_turn_last": (
            "" if stats["merge_marker_turn_last"] is None else stats["merge_marker_turn_last"]
        ),
        "tail_turns": stats["tail_turns"],
        "tail_mandated_turns": stats["tail_mandated_turns"],
        "bucket_tail_cr": stats["bucket_tail_cr"],
        "bucket_vg_cr": stats["bucket_vg_cr"],
        "bucket_micro_cr": stats["bucket_micro_cr"],
        "vg_second_turn": "" if stats["vg_second_turn"] is None else stats["vg_second_turn"],
        "first_turn_cache_write": stats["first_turn_cache_write"],
        "excess_file_reads": stats["excess_file_reads"],
        "pr_numbers": ";".join(str(n) for n in stats["pr_numbers"]),
        "entry_skill": stats["entry_skill"] or "",
        "path": str(path),
    }


def session_rollup(rows: list[dict]) -> list[dict]:
    """Aggregate per-agent rows into one record per (project, session)."""
    sessions: dict[tuple, dict] = {}
    for r in rows:
        key = (r["project"], r["session_id"])
        s = sessions.setdefault(
            key,
            {
                "project": r["project"],
                "session_id": r["session_id"],
                "entry_skill": "",
                "agents": 0,
                "cost_usd": 0.0,
                "turns": 0,
                "first_date": r["date"],
            },
        )
        s["agents"] += 1
        s["cost_usd"] += r["cost_usd"]
        s["turns"] += r["turns"]
        if r["agent_id"] == "main" and r["entry_skill"]:
            s["entry_skill"] = r["entry_skill"]
    out = sorted(sessions.values(), key=lambda s: -s["cost_usd"])
    for s in out:
        s["cost_usd"] = round(s["cost_usd"], 4)
    return out


def run_census(projects_dir: Path, days: int) -> tuple[list[dict], dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = []
    files_seen = 0
    files_skipped_old = 0
    files_unreadable = 0
    corpus_skipped_lines = 0
    corpus_total_lines = 0
    for project, session_id, agent_id, path in iter_trace_files(projects_dir):
        files_seen += 1
        try:
            stats = parse_trace_file(path)
        except OSError as e:
            log.warning("unreadable %s: %s", path, e)
            files_unreadable += 1
            continue
        corpus_skipped_lines += stats["skipped_lines"]
        corpus_total_lines += stats["total_lines"]
        if stats["last_ts"] is None or stats["last_ts"] < cutoff:
            files_skipped_old += 1
            continue
        rows.append(build_row(project, session_id, agent_id, path, stats))
    meta = {
        "files_seen": files_seen,
        "files_in_window": len(rows),
        "files_skipped_old_or_undated": files_skipped_old,
        "files_unreadable": files_unreadable,
        "corpus_skipped_lines": corpus_skipped_lines,
        "corpus_total_lines": corpus_total_lines,
    }
    return rows, meta


def summarize(rows: list[dict], meta: dict, days: int) -> dict:
    totals = {k: sum(r[k] for r in rows) for k in USAGE_KEYS}
    total_lines = sum(r["total_lines"] for r in rows)
    skipped_lines = sum(r["skipped_lines"] for r in rows)
    return {
        "window_days": days,
        **meta,
        "sessions": len({(r["project"], r["session_id"]) for r in rows}),
        "totals": {
            **totals,
            "cost_usd": round(sum(r["cost_usd"] for r in rows), 2),
            "turns": sum(r["turns"] for r in rows),
            "synthetic_messages": sum(r["synthetic_messages"] for r in rows),
            "unknown_model_messages": sum(r["unknown_model_messages"] for r in rows),
        },
        "skipped_lines": skipped_lines,
        "total_lines": total_lines,
        "skipped_line_pct": round(100 * skipped_lines / total_lines, 3) if total_lines else 0.0,
        "rollup": session_rollup(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Census of Claude Code session traces: one CSV row per agent."
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path("~/.claude/projects").expanduser(),
        help="Root of the trace corpus (default: ~/.claude/projects)",
    )
    parser.add_argument("--days", type=int, default=28, help="Window in days (default 28)")
    parser.add_argument("--output", type=Path, help="Write per-agent rows to this CSV")
    parser.add_argument(
        "--json", action="store_true", help="Print the summary as JSON to stdout"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    rows, meta = run_census(args.projects_dir, args.days)

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        log.info("wrote %d rows to %s", len(rows), args.output)

    summary = summarize(rows, meta, args.days)
    if args.json:
        json.dump(summary, sys.stdout, indent=2, default=str)
        print()
    else:
        log.info(
            "files=%d sessions=%d cost=$%s skipped_lines=%s%%",
            summary["files_in_window"],
            summary["sessions"],
            summary["totals"]["cost_usd"],
            summary["skipped_line_pct"],
        )


if __name__ == "__main__":
    main()
