#!/usr/bin/env python3
"""Trace-friction scan (ticket 1169): velocity losses in agent transcripts.

Zero-LLM, standard-library-only companion to trace-stats.py: that measures
cost, this measures friction. Method: design/2026-10-21-velocity-friction-scan.md.

Walks ~/.claude/projects (main sessions and subagents), pairs each tool_use
with its tool_result, and reports per day:

* tool calls and tool errors, errors split by cause (worktree-guard refusal,
  "No such tool available", Write-outside-worktree, other);
* calls slower than 30 s, by tool;
* Bash commands matching the wait regex;
* follies (ticket 1217): detectors for self-matching pgrep waiters, sleep loops
  that ran to their cap, and an identical failing command repeated, each with a
  duration bound and the rung of the barrier ladder it maps to (data only);
* barrier denials: how often each worktree guard refused a call (counts only;
  a verdict on a barrier belongs to /test-doctor).

Runtimes (ticket 1517): by default it reads, besides Claude Code, this host's
Codex rollouts, Pi sessions and Pi spool (scripts/trace_corpora.py). The daily
series and totals sum every runtime read; `runtimes` names each one read, not
read and could not look at, with its own counts and `not_measured` map. A Codex
call whose output records no script status and no exit code is counted in
`calls_outcome_unknown`, neither as an error nor as a success.

`--pi-runs DIR` reads the arena's Pi sessions instead and never emits a
command text.

The series is DAILY on purpose: period totals hid that guard refusals stopped
on 2026-10-15. Totals are derived from the series.

Limits, stated in the output as well: a duration is tool_use timestamp to
tool_result timestamp, so it includes permission waits and background
commands, an UPPER BOUND on tool wall-clock. The wait regex runs on the command
with quoted strings and heredoc bodies removed. Cause classes are
message-text heuristics; "other" is the residual.
"""

import argparse
import csv
import importlib.util
import json
import logging
import os
import re
import shlex
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

log = logging.getLogger("trace-friction")

_HERE = Path(__file__).resolve().parent


def _sibling(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


corpora = _sibling("trace_corpora", "trace_corpora.py")
_te = _sibling("trace_events", "trace_events.py")

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
# Applied to strip_quoted(command), so quoted or heredoc text cannot match.
WAIT_RE = re.compile(
    r"(?:^|[;&|(]\s*|\n\s*|\b(?:do|then|else)\s+|\btimeout\s+\d+\w*\s+)"
    r"(?:sleep\s+\d|until\s)"
    r"|--watch\b|\bgh\s+(?:run|pr\s+checks)\s+watch\b"
)
# A wait-roster.py call (ticket 1327) is the same wait moved into a helper:
# counted, or the series would drop as the recipes adopt it with no less
# waiting. The recipes quote its path, so this one matches the raw command, at
# command position only (optionally behind python3 or timeout N).
WAIT_HELPER_RE = re.compile(
    r"(?:^|[;&|(]\s*|\n\s*|\b(?:do|then|else)\s+|\btimeout\s+\d+\w*\s+)"
    r"(?:python3?\s+)?[\"']?[^\s\"';&|]*wait-roster\.py\b"
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


HEREDOC_RE = re.compile(
    r"<<-?[ \t]*(['\"]?)(\w+)\1[^\n]*\n(.*?)(?:\n[ \t]*\2[ \t]*(?=\n|$)|\Z)", re.S
)
SUBST_RE = re.compile(r"\$\(([^()]*)\)")


def _quoted_spans(cmd: str) -> list[tuple[int, int]]:
    """Spans of heredoc bodies and quoted strings (quotes included)."""
    spans: list[tuple[int, int]] = []
    for m in HEREDOC_RE.finditer(cmd):
        spans.append((m.start(3), m.end(3)))
    i, n = 0, len(cmd)
    while i < n:
        if any(a <= i < b for a, b in spans):
            i = next(b for a, b in spans if a <= i < b)
            continue
        c = cmd[i]
        if c == "\\":
            i += 2
        elif c in "'\"":
            j = i + 1
            while j < n and cmd[j] != c:
                j += 2 if (c == '"' and cmd[j] == "\\") else 1
            spans.append((i, min(j + 1, n)))
            i = j + 1
        else:
            i += 1
    return sorted(spans)


def strip_quoted(cmd: str) -> str:
    """Drop heredoc bodies and quoted strings; keep $(...) found inside them."""
    out, pos = [], 0
    for a, b in _quoted_spans(cmd):
        if a < pos:
            continue
        out.append(cmd[pos:a])
        out.extend(f" {m.group(1)} " for m in SUBST_RE.finditer(cmd[a:b]))
        pos = b
    out.append(cmd[pos:])
    return "".join(out)


def is_wait_command(command: str) -> bool:
    return bool(WAIT_RE.search(strip_quoted(command)) or WAIT_HELPER_RE.search(command))


def _parse_ts(s) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        ts = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


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
        "calls_outcome_unknown": 0,
        "denials": Counter(),
    }


def merge_day(into: dict, day: dict) -> None:
    """Add one runtime's day into the all-runtime day."""
    for k, v in day.items():
        if k == "errors_by_cause":
            for c, n in v.items():
                into[k][c] += n
        elif k == "slow_by_tool":
            for tool, e in v.items():
                t = into[k].setdefault(tool, {"calls": 0, "seconds": 0.0})
                t["calls"] += e["calls"]
                t["seconds"] += e["seconds"]
        elif k == "denials":
            into[k].update(v)
        else:
            into[k] += v


# --- follies (ticket 1217) ---------------------------------------------------
# folly -> rung of the barrier ladder (fix the primitive, per-command cap in the
# tool layer, PreToolUse hook, instruction last). Data only: a table, not an
# engine; applying a barrier is a separate reviewed change.
FOLLY_RUNG = {
    "pgrep_self_match": "fix_primitive",
    "sleep_poll_to_cap": "fix_primitive",
    "repeat_failing": "hook",
}
DEFAULT_TIMEOUT_S = 120.0  # Claude Code Bash default; lower bound only
PGREP_RE = re.compile(
    r"(?:^|[;&|(!\n]|\b(?:do|then|else|until|while|if)\b|\$\()\s*(pgrep)\b(.*)"
)
PGREP_ARG_OPTS = set("uUgGPstnO")  # short options that take an argument
LOOP_RE = re.compile(r"\b(?:for|while|until)\b")
SLEEP_RE = re.compile(r"\bsleep\s+((?:\d+(?:\.\d+)?[smhd]?)+)")
SLEEP_PART_RE = re.compile(r"(\d+(?:\.\d+)?)([smhd]?)")
SLEEP_UNIT = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}
SEQ_RE = re.compile(r"\bseq\s+(?:(\d+)\s+)?(\d+)|\{(\d+)\.\.(\d+)\}")
UNBOUNDED_RE = re.compile(r"\b(?:while\s+(?:true|:)|until\s+false)\b|\buntil\s+!?\s*\S")


def _argv(rest: str) -> list[str]:
    """Tokens of the pgrep arguments, up to the first shell operator."""
    lex = shlex.shlex(rest, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    out: list[str] = []
    try:
        for tok in lex:
            if re.fullmatch(r"[();<>|&]+", tok):
                break
            out.append(tok)
    except ValueError:  # unbalanced quote
        pass
    return out


def folly_pgrep_self(cmd: str) -> bool:
    """True when a `pgrep -f PATTERN` pattern matches the command's own text.

    The Bash tool runs `bash -c '<whole text>'`, so a pattern that occurs in the
    command matches the waiting shell itself. The bracket idiom does not: the
    regex `[p]adme` does not match the literal text `[p]adme`. pkill is left
    out: it kills rather than waits, and its failure costs no stall.
    """
    spans = _quoted_spans(cmd)
    for m in PGREP_RE.finditer(cmd):
        if any(a <= m.start(1) < b for a, b in spans):
            continue  # the word sits inside quoted text: not a call
        argv = _argv(m.group(2))
        pattern, full, skip = None, False, False
        for tok in argv:
            if skip:
                skip = False
            elif tok.startswith("--"):
                continue
            elif tok.startswith("-"):
                full = full or "f" in tok
                skip = bool(tok[-1] in PGREP_ARG_OPTS and len(tok) > 1)
            elif pattern is None and not re.match(r"\d?[<>]", tok):
                pattern = tok  # first positional; redirections are not patterns
        if not (full and pattern):
            continue
        try:
            if re.search(pattern, cmd):
                return True
        except re.error:
            continue
    return False


def folly_sleep_to_cap(cmd: str, duration_s: float, timeout_s: float | None = None) -> bool:
    """True when a sleep loop ran to (at least 90 % of) its cap.

    The cap is the loop's own: iterations x sleep for a counted loop, the call
    timeout for a condition loop. A loop that ended earlier met its condition.
    """
    text = strip_quoted(cmd)
    sleeps = SLEEP_RE.findall(text)
    if not sleeps or not LOOP_RE.search(text):
        return False
    step = sum(float(n) * SLEEP_UNIT[u] for n, u in SLEEP_PART_RE.findall(sleeps[0]))
    seq = SEQ_RE.search(text)
    if seq:
        lo, hi = (seq.group(1), seq.group(2)) if seq.group(2) else (seq.group(3), seq.group(4))
        cap = (int(hi) - int(lo or 1) + 1) * step
    elif timeout_s and UNBOUNDED_RE.search(text):
        cap = timeout_s
    else:
        return False
    return cap > 0 and duration_s >= 0.9 * cap


def _normalize(cmd: str) -> str:
    return " ".join(cmd.split())


def repeat_failing_calls(calls: list[dict]) -> list[dict]:
    """Calls that repeat the immediately preceding failed Bash command.

    "In a row" means no other call between, so an Edit, a Write or any
    different command resets the run.
    """
    hits, prev = [], None
    for c in calls:
        key = _normalize(c["cmd"]) if c["tool"] == "Bash" and c["cmd"] else None
        if key and c["is_error"] and key == prev:
            hits.append(c)
        prev = key if key and c["is_error"] else None
    return hits


class Follies:
    """Accumulator: per folly count, sessions, duration bounds, runtime split."""

    def __init__(self, min_seconds: float = 0.0) -> None:
        self.rows: dict[str, dict] = {}
        self.min_seconds = min_seconds  # count only calls at least this long

    def add(self, folly: str, session: str, call: dict, runtime: str) -> None:
        secs = max((call["end"] - call["start"]).total_seconds(), 0.0)
        if secs < self.min_seconds:
            return
        if call.get("measured"):
            low = secs
        else:
            low = min(secs, call.get("timeout_s") or DEFAULT_TIMEOUT_S)
        r = self.rows.setdefault(
            folly, {"count": 0, "sessions": set(), "ub": 0.0, "lb": 0.0, "runtime": Counter()}
        )
        r["count"] += 1
        r["sessions"].add(session)
        r["ub"] += secs
        r["lb"] += low
        r["runtime"][runtime] += 1

    def scan(self, calls: list[dict], session: str, runtime: str) -> None:
        for c in calls:
            if c["tool"] != "Bash" or not c["cmd"]:
                continue
            secs = max((c["end"] - c["start"]).total_seconds(), 0.0)
            if folly_pgrep_self(c["cmd"]):
                self.add("pgrep_self_match", session, c, runtime)
            # Claude Code backgrounds a call at its timeout (default 120 s);
            # Pi sessions record none, so a condition loop has no known cap there.
            cap = c.get("timeout_s") or (DEFAULT_TIMEOUT_S if runtime == "claude-code" else None)
            if folly_sleep_to_cap(c["cmd"], secs, cap):
                self.add("sleep_poll_to_cap", session, c, runtime)
        for c in repeat_failing_calls(calls):
            self.add("repeat_failing", session, c, runtime)

    def report(self) -> dict:
        return {
            k: {
                "count": r["count"],
                "sessions": len(r["sessions"]),
                "seconds_upper_bound": round(r["ub"], 1),
                "seconds_lower_bound": round(r["lb"], 1),
                "rung": FOLLY_RUNG[k],
                "runtime": dict(r["runtime"]),
            }
            for k, r in sorted(self.rows.items())
        }


FOLLIES_NOTE = (
    "counts and seconds are bounds: the upper bound is the call's tool_use to "
    "tool_result span; the lower bound caps it at the call timeout (default "
    f"{DEFAULT_TIMEOUT_S:.0f} s) on Claude Code and equals it where the runtime "
    "records the duration (Pi). Traces do not record when a job ended, so no "
    "hours are given back; sessions count distinct transcripts"
)
BLOCKED_RE = re.compile(r"\bBLOCKED:|PreToolUse:[\w|]* ?hook error")


# --- readers: Claude Code and Pi shapes -> one call record -------------------
def _calls(path: Path, skipped: list) -> "Iterator[dict]":
    """Yield paired calls of one Claude Code transcript; count unreadable lines."""
    pending: dict[str, tuple[datetime, str, str, float | None]] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                skipped[0] += 1
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
                tid = block.get("id") if kind == "tool_use" else block.get("tool_use_id")
                if not isinstance(tid, str):
                    continue
                if kind == "tool_use":
                    inp = block.get("input")
                    inp = inp if isinstance(inp, dict) else {}
                    to = inp.get("timeout")
                    to = to / 1000 if isinstance(to, (int, float)) else None
                    pending[tid] = (ts, str(block.get("name", "?")), str(inp.get("command", "")), to)
                elif kind == "tool_result" and tid in pending:
                    start, tool, cmd, to = pending.pop(tid)
                    yield {
                        "id": tid, "start": start, "end": ts, "tool": tool, "cmd": cmd,
                        "is_error": bool(block.get("is_error")),
                        "text": _result_text(block.get("content")), "timeout_s": to,
                    }  # fmt: skip


def _pi_calls(path: Path, skipped: list) -> "Iterator[dict]":
    """Yield paired calls of one Pi session; unknown line types are counted."""
    pending: dict[str, tuple[datetime, str, str, float | None]] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                skipped[0] += 1
                continue
            msg = row.get("message") if isinstance(row, dict) else None
            ts = _parse_ts(row.get("timestamp")) if isinstance(row, dict) else None
            if row.get("type") != "message" or not isinstance(msg, dict) or ts is None:
                skipped[0] += 1
                continue
            content = msg.get("content")
            if msg.get("role") == "assistant" and isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "toolCall" and isinstance(b.get("id"), str):
                        args = b.get("arguments")
                        args = args if isinstance(args, dict) else {}
                        to = args.get("timeout")
                        to = float(to) if isinstance(to, (int, float)) else None
                        tool = "Bash" if b.get("name") == "bash" else str(b.get("name", "?"))
                        pending[b["id"]] = (ts, tool, str(args.get("command", "")), to)
            elif msg.get("role") == "toolResult" and msg.get("toolCallId") in pending:
                start, tool, cmd, to = pending.pop(msg["toolCallId"])
                ms = msg.get("durationMs")
                measured = isinstance(ms, (int, float))
                end = start + timedelta(milliseconds=ms) if measured else ts
                yield {
                    "id": msg["toolCallId"], "start": start, "end": end, "tool": tool,
                    "cmd": cmd, "is_error": bool(msg.get("isError")),
                    "text": _result_text(content), "timeout_s": to, "measured": measured,
                }  # fmt: skip


CODEX_SHELLS = {"exec", "local_shell_call"} | _te.SHELL_TOOLS
CODEX_SCRIPT = re.compile(r"\AScript (completed|failed)\b")
CODEX_EXIT_ANY = re.compile(r"(?:exit_code\W{0,4}|exited with code\s*|exit code:?\s*)(-?\d+)", re.I)


def codex_outcome(text: str) -> bool | None:
    """Error (True), success (False) or unknown (None) of one Codex call output.

    The `exec` tool runs a script: its output opens with `Script completed` or `Script failed`,
    and the commands it ran record `exit_code`. An error is a failed script or any non-zero exit
    code, so a completed script whose command failed counts as an error, as a failed Bash call does
    on Claude Code. An output with neither marker has an unknown outcome."""
    script = CODEX_SCRIPT.match(text)
    codes = [int(c) for c in CODEX_EXIT_ANY.findall(text)]
    if (script and script.group(1) == "failed") or any(codes):
        return True
    if script or codes:
        return False
    return None


def _codex_calls(path: Path, skipped: list) -> "Iterator[dict]":
    """Yield paired calls of one Codex rollout. A shell call is named Bash; its outcome is
    codex_outcome of its output text."""
    pending: dict[str, tuple[datetime, str, str]] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                skipped[0] += 1
                continue
            payload = row.get("payload") if isinstance(row, dict) else None
            ts = _parse_ts(row.get("timestamp")) if isinstance(row, dict) else None
            if row.get("type") != "response_item" or not isinstance(payload, dict) or ts is None:
                continue
            ptype = payload.get("type") or ""
            if ptype in _te.CODEX_CALLS:
                cid = payload.get("call_id") or payload.get("id")
                name = str(payload.get("name") or ptype)
                cmd = _te.codex_command(payload) or ""
                tool = "Bash" if name in CODEX_SHELLS or ptype == "local_shell_call" else name
                if isinstance(cid, str):
                    pending[cid] = (ts, tool, cmd)
            elif ptype.endswith("_output") and payload.get("call_id") in pending:
                start, tool, cmd = pending.pop(payload["call_id"])
                text = _te._result_text(payload.get("output"))  # Codex blocks are `input_text`
                yield {
                    "id": payload["call_id"], "start": start, "end": ts, "tool": tool, "cmd": cmd,
                    "is_error": codex_outcome(text),
                    "text": text, "timeout_s": None,
                }  # fmt: skip


READERS = {"claude-code": _calls, "pi": _pi_calls, "codex": _codex_calls}
FOLLY_RUNTIME = {corpora.CLAUDE: "claude-code", corpora.CODEX: "codex", corpora.PI: "pi", corpora.PI_SPOOL: "pi"}
NOT_MEASURED = {
    corpora.CODEX: {
        "outcome of calls whose output records no script status or exit code (agent and message "
        "tools)": "counted in calls_outcome_unknown, neither as an error nor as a success",
        "sleep_poll_to_cap on condition loops": "a rollout records no call timeout, so an uncounted loop has no known cap",
    },
    corpora.PI: {"sleep_poll_to_cap on condition loops": "Pi records no default call timeout; only a call's own timeout caps a loop"},
}
NOT_MEASURED[corpora.PI_SPOOL] = NOT_MEASURED[corpora.PI]


def scan_file(path: Path, cutoff: datetime, seen: set, days: dict,
              follies: Follies | None = None, pi: bool = False,
              runtime: str | None = None) -> int:  # fmt: skip
    """Fold one transcript into the per-day table; return skipped line count."""
    runtime = runtime or ("pi" if pi else "claude-code")
    skipped = [0]
    kept = []
    for call in READERS[runtime](path, skipped):
        key = call["id"] if runtime == "claude-code" else (str(path), call["id"])
        if key in seen or call["start"] < cutoff:
            continue  # resumed sessions replay parent rows
        seen.add(key)
        kept.append(call)
        _record(days, call)
    if follies is not None:
        follies.scan(kept, path.stem, runtime)
    return skipped[0]


def _record(days: dict, call: dict) -> None:
    start, end, tool, cmd = call["start"], call["end"], call["tool"], call["cmd"]
    day = days[start.date().isoformat()]
    secs = max((end - start).total_seconds(), 0.0)
    day["calls"] += 1
    if call["is_error"] is None:
        day["calls_outcome_unknown"] += 1
    if tool == "Bash":
        day["bash_calls"] += 1
        if is_wait_command(cmd):
            day["wait_commands"] += 1
            day["wait_seconds"] += secs
    if call["is_error"]:
        cause = classify_error(tool, call["text"])
        day["errors"] += 1
        day["errors_by_cause"][cause] += 1
        day["error_seconds"] += secs
        if cause in ("worktree_guard", "write_outside_worktree"):
            day["denials"][cause] += 1
        elif BLOCKED_RE.search(call["text"]):
            day["denials"]["unattributed"] += 1
    if secs > SLOW_SECONDS:
        day["slow_calls"] += 1
        day["slow_seconds"] += secs
        entry = day["slow_by_tool"].setdefault(tool, {"calls": 0, "seconds": 0.0})
        entry["calls"] += 1
        entry["seconds"] += secs


def run_scan(roots, days: int, now: datetime | None = None,
             min_seconds: float = 0.0) -> dict:  # fmt: skip
    """Scan every corpus in `roots` (runtime name -> root; a bare path is Claude Code's alone)."""
    roots = corpora.normalize_roots(roots)
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    table: dict[str, dict] = defaultdict(new_day)
    follies = Follies(min_seconds)
    files = skipped = 0
    entries = []
    for name in corpora.CORPORA:
        root = roots.get(name)
        if root is None:
            entries.append(corpora.entry(name, None, "not read", "no corpus root given"))
            continue
        rt_table: dict[str, dict] = defaultdict(new_day)
        try:
            if name == corpora.CLAUDE:
                if not Path(root).is_dir():
                    raise corpora.CouldNotLook(f"no trace corpus at {root}")
                paths = list(iter_trace_files(Path(root), cutoff.timestamp()))
            else:
                paths = corpora.recent_files(name, Path(root), cutoff.timestamp())
        except (corpora.CouldNotLook, OSError) as e:
            entries.append(corpora.entry(name, root, "could not look", str(e)))
            continue
        seen: set = set()
        rt_files = rt_skipped = unreadable = 0
        for path in paths:
            try:
                rt_skipped += scan_file(path, cutoff, seen, rt_table, follies, runtime=FOLLY_RUNTIME[name])
            except OSError as e:
                log.warning("unreadable %s: %s", path, e)
                unreadable += 1
                continue
            rt_files += 1
        if paths and unreadable == len(paths):
            entries.append(corpora.entry(name, root, "could not look",
                                         f"none of its {len(paths)} transcripts under {root} could be read"))
            continue
        for d, day in rt_table.items():
            merge_day(table[d], day)
        files += rt_files
        skipped += rt_skipped
        days_ = rt_table.values()
        measures = {k: sum(d[k] for d in days_) for k in
                    ("calls", "bash_calls", "errors", "calls_outcome_unknown", "slow_calls", "wait_commands")}
        entries.append(corpora.entry(name, root, "read", files=rt_files, unreadable_files=unreadable,
                                     skipped_lines=rt_skipped, **measures,
                                     **({"not_measured": NOT_MEASURED[name]} if name in NOT_MEASURED else {})))
    series = [{"date": d, **table[d]} for d in sorted(table)]
    out = summarize(series, days, files, skipped, follies)
    out.update(corpora.report_keys(entries))
    return out


def iter_pi_files(runs_dir: Path):
    """Yield Pi session files under an arena run directory (or its parent)."""
    for pattern in ("*/attempts/*/sessions/*.jsonl", "runs-*/*/attempts/*/sessions/*.jsonl"):
        yield from sorted(runs_dir.glob(pattern))


def run_pi_scan(runs_dir: Path, now: datetime | None = None,
                min_seconds: float = 0.0) -> dict:  # fmt: skip
    """Same summary over Pi sessions. Every session counts (no window); no
    command text is carried into the result."""
    table: dict[str, dict] = defaultdict(new_day)
    seen: set = set()
    follies = Follies(min_seconds)
    files = skipped = 0
    floor = datetime.min.replace(tzinfo=timezone.utc)
    for path in iter_pi_files(runs_dir):
        try:
            skipped += scan_file(path, floor, seen, table, follies, pi=True)
        except OSError as e:
            log.warning("unreadable %s: %s", path, e)
            continue
        files += 1
    series = [{"date": d, **table[d]} for d in sorted(table)]
    out = summarize(series, 0, files, skipped, follies)
    out.pop("window_days")
    out["runtime"] = "pi"
    return out


def summarize(series: list[dict], days: int, files: int, skipped: int,
              follies: Follies | None = None) -> dict:  # fmt: skip
    causes: Counter = Counter()
    denials: Counter = Counter()
    tail: dict[str, dict] = {}
    for d in series:
        causes.update(d["errors_by_cause"])
        denials.update(d.get("denials", {}))
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
        "wait_note": "wait regex runs on the command minus quoted strings and heredoc bodies",
        "follies": follies.report() if follies else {},
        "follies_note": FOLLIES_NOTE,
        "folly_barrier": dict(FOLLY_RUNG),
        "barrier_denials": {
            "worktree_guard": denials.get("worktree_guard", 0),
            "write_outside_worktree": denials.get("write_outside_worktree", 0),
            "unattributed": denials.get("unattributed", 0),
        },
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
            "calls_outcome_unknown": sum(d.get("calls_outcome_unknown", 0) for d in series),
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
        description="Daily friction series and follies from Claude Code, Codex and Pi traces, "
        "or the arena's Pi sessions with --pi-runs."
    )
    corpora.add_root_flags(parser)
    parser.add_argument(
        "--days", type=int, default=28, help="Window in days (default 28)"
    )
    parser.add_argument(
        "--output", type=Path, help="Write the daily series to this CSV"
    )
    parser.add_argument(
        "--pi-runs",
        type=Path,
        help="Arena run directory (or its parent) holding Pi sessions "
        "(*/attempts/*/sessions/*.jsonl); replaces the scan of this host's corpora",
    )
    parser.add_argument(
        "--folly-min-seconds", type=float, default=0.0,
        help="Count follies only for calls at least this long (the census uses 45)",
    )  # fmt: skip
    parser.add_argument("--json", action="store_true", help="Print the summary as JSON")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.pi_runs:
        summary = run_pi_scan(args.pi_runs, min_seconds=args.folly_min_seconds)
    else:
        summary = run_scan(corpora.roots_from_args(args), args.days, min_seconds=args.folly_min_seconds)
        if corpora.none_read(summary["runtimes"]):
            sys.exit(1)
    if args.output:
        write_csv(args.output, summary)
        log.info("wrote %d days to %s", len(summary["daily"]), args.output)
    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        print()
        return
    for line in corpora.render(summary.get("runtimes", []), "{files} transcripts, {calls} calls"):
        print(line)
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
