#!/usr/bin/env python3
"""One event model over the transcripts of every runtime (ticket 1385; memo conception/2026-10-31-monitoring-redesign.md 4.4).

A reader turns one transcript into `Event`s with the same fields whatever the runtime: Claude Code
(with its `subagents/`), Codex rollouts, Pi sessions, and a file-only event for runtimes with no
structured log (aider, vibe). It is the reader a later index will reuse (memo section 5), so it holds no
rendering code and no CLI; `trace_timeline.py` renders.

Event kinds:
    agent  the span of one session, subagent or seat; tokens and shadow USD are the sum of its turns
    turn   one model request; tokens are per request (Codex: differences of the cumulative counter)
    tool   one tool call, start at the call, end at its result (Claude: at the completion notification
           when the call went to the background)

Pointer `(file, call id)` names the transcript and the runtime's own id (`tool_use_id`, Codex `call_id`,
Pi `toolCallId`; a turn's message id or turn id; None for aider/vibe: file only). The file is the path
relative to its live root, so it resolves in the live tree and in the archive alike; there are no line
numbers, which a re-copy would stale.

Shadow USD is what the tokens would cost at API list price. `shadow_usd` is None when the model has no
price row, and a renderer must say `cost unknown`, never 0. `cost_source` says where the number came from:
`price-table`, `pi-recorded` (Pi's own record, a recorded 0 for a local model stays 0), or `unpriced`.

Stdlib only. Readers take an iterable of JSONL lines; a malformed line is skipped, never fatal.
"""
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

# $/MTok, per category. Source: claude-api skill pricing tables (2026-06).
# Cache read = 0.1x input; 5m cache write = 1.25x; 1h cache write = 2x.
# trace-stats.py re-exports this table and resolve_pricing (four scripts spec-load it); its keys, notably
# `cache_write_5m`, are read by trace-hypotheses.py, so OpenAI rows live in their own table below.
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

# $/MTok, OpenAI standard tier, text tokens. Source: https://platform.openai.com/docs/pricing
# (same page as https://developers.openai.com/api/docs/pricing), "Standard" pane, "Prompt caching" table
# (columns Input, Output, Cached input, 30m write, 12h write), fetched 2026-10-31. Only models seen in the
# local Codex rollouts (~/.codex/sessions) are listed; `cache_write` is the 30m-write column. Not listed,
# hence `cost unknown`: codex-auto-review (no page row), gpt-5.5 (page rows depend on a 272K context tier and
# list no cache write), and any other id. Never price a model from memory.
OPENAI_PRICING = {
    "gpt-6-astra": {"input": 10.0, "output": 50.0, "cache_read": 1.0, "cache_write": 12.5},
    "gpt-6.1-sol": {"input": 2.0, "output": 10.0, "cache_read": 0.1, "cache_write": 2.5},
    "gpt-6-sol": {"input": 2.0, "output": 10.0, "cache_read": 0.2, "cache_write": 2.5},
    "gpt-6-luna": {"input": 0.1, "output": 0.5, "cache_read": 0.01, "cache_write": 0.125},
    "gpt-5.6-sol": {"input": 4.0, "output": 20.0, "cache_read": 0.4, "cache_write": 5.0},
    "gpt-5.6-terra": {"input": 2.0, "output": 12.0, "cache_read": 0.2, "cache_write": 2.5},
    "gpt-5.6-luna": {"input": 0.2, "output": 1.2, "cache_read": 0.02, "cache_write": 0.25},
}


@dataclass(frozen=True)
class Event:
    kind: str  # "agent" | "turn" | "tool"
    name: str  # tool name, or the agent label
    start: float  # epoch seconds
    end: float
    runtime: str  # claude | codex | pi | aider | vibe
    agent: str  # id of the agent the event belongs to (the lane key)
    parent_agent: str | None
    model: str | None
    tokens: dict | None  # input (uncached), output, cache_read, cache_write
    shadow_usd: float | None  # None = unpriced: "cost unknown", never 0
    cost_source: str  # "price-table" | "pi-recorded" | "unpriced"
    exit: int | None
    pointer: tuple  # (file relative to its root, call id or None)
    detail: str | None = None


def resolve_pricing(model_id: str) -> dict | None:
    """Map a Claude model id to its pricing family; None for unknown models."""
    for family in ("fable", "opus", "sonnet", "haiku"):
        if family in model_id:
            return PRICING[family]
    return None


def claude_cost(model: str, usage: dict) -> float | None:
    """Dollars for one Claude message's usage; None when the model is not in the table."""
    p = resolve_pricing(model or "")
    if p is None:
        return None
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


def openai_cost(model: str, tokens: dict) -> float | None:
    """Dollars for OpenAI tokens (input = uncached); None when the model has no price row."""
    row = OPENAI_PRICING.get((model or "").removeprefix("openai/"))
    if row is None:
        return None
    return (
        tokens.get("input", 0) * row["input"]
        + tokens.get("output", 0) * row["output"]
        + tokens.get("cache_read", 0) * row["cache_read"]
        + tokens.get("cache_write", 0) * row["cache_write"]
    ) / 1_000_000


def epoch(stamp) -> float | None:
    """ISO 8601 text (or epoch milliseconds) to epoch seconds; None when unreadable."""
    if isinstance(stamp, (int, float)):
        return stamp / 1000 if stamp > 1e11 else float(stamp)
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def _rows(lines: Iterable[str]):
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            yield row


def _sum_cost(turns: list[Event]) -> tuple[float | None, str]:
    """Shadow USD of an agent: the turns' sum; None as soon as one turn is unpriced."""
    if not turns or any(t.shadow_usd is None for t in turns):
        return None, "unpriced"
    sources = {t.cost_source for t in turns}
    return sum(t.shadow_usd for t in turns), sources.pop() if len(sources) == 1 else "mixed"


def _sum_tokens(turns: list[Event]) -> dict | None:
    keys = ("input", "output", "cache_read", "cache_write")
    got = [t.tokens for t in turns if t.tokens]
    return {k: sum(t.get(k, 0) for t in got) for k in keys} if got else None


def _span(runtime, name, agent, parent, file, turns, times, model, call_id=None) -> Event:
    usd, source = _sum_cost(turns)
    start = min(times) if times else 0.0
    return Event("agent", name, start, max(times) if times else start, runtime, agent, parent, model,
                 _sum_tokens(turns), usd, source, None, (file, call_id))


def _result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return ""


NOTIFICATION_ID = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")


def read_claude(lines: Iterable[str], file: str, agent: str | None = None,
                parent_agent: str | None = None, name: str = "claude session") -> list[Event]:
    """Claude Code main session or subagent file.

    Usage is counted once per `message.id` (rows repeat per content block). A tool call ends at its
    `tool_result`; a call that went to the background ends at the later `<task-notification>` naming its
    `tool_use_id`.
    """
    turns: dict[str, dict] = {}
    pending: dict[str, dict] = {}
    notified: dict[str, float] = {}
    tools: list[Event] = []
    times: list[float] = []
    prev = None
    model = None
    for row in _rows(lines):
        ts = epoch(row.get("timestamp"))
        kind = row.get("type")
        agent = agent or row.get("sessionId")
        if kind == "queue-operation" and row.get("operation") == "enqueue":
            content = row.get("content")
            if isinstance(content, str) and content.lstrip().startswith("<task-notification>") and ts:
                for tid in NOTIFICATION_ID.findall(content):
                    notified.setdefault(tid, ts)
            continue
        if ts is None or kind not in ("assistant", "user"):
            continue
        times.append(ts)
        message = row.get("message") or {}
        content = message.get("content")
        if kind == "assistant":
            mid = message.get("id") or f"row-{len(turns)}"
            turn = turns.get(mid)
            if turn is None:
                turn = turns[mid] = {"start": prev if prev is not None else ts, "model": message.get("model")}
            turn["end"] = ts
            turn["usage"] = message.get("usage") or turn.get("usage") or {}
            if message.get("model") and message["model"] != "<synthetic>":
                model = message["model"]
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id"):
                    inp = block.get("input") if isinstance(block.get("input"), dict) else {}
                    pending[block["id"]] = {"name": block.get("name") or "?", "start": ts,
                                            "model": message.get("model"),
                                            "detail": inp.get("description") or inp.get("subagent_type")}
        else:
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    call = pending.get(block.get("tool_use_id"))
                    if call is not None and "end" not in call:
                        call["end"] = ts
                        call["exit"] = 1 if block.get("is_error") else 0
        prev = ts
    last = max(times) if times else 0.0
    for call_id, call in pending.items():
        end = call.get("end", last)
        if call_id in notified and notified[call_id] > end:
            end = notified[call_id]  # background call: done at its completion notification
            times.append(end)
        tools.append(Event("tool", call["name"], call["start"], end, "claude", agent or "?", parent_agent,
                           call["model"], None, None, "unpriced", call.get("exit"), (file, call_id),
                           call["detail"]))
    turn_events = []
    for mid, turn in turns.items():
        if turn["model"] == "<synthetic>":
            continue  # harness-injected, no API cost (trace-stats.py rule)
        usage = turn["usage"]
        tokens = {"input": usage.get("input_tokens", 0) or 0, "output": usage.get("output_tokens", 0) or 0,
                  "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
                  "cache_write": usage.get("cache_creation_input_tokens", 0) or 0}
        usd = claude_cost(turn["model"], usage)
        turn_events.append(Event("turn", "turn", turn["start"], turn["end"], "claude", agent or "?",
                                 parent_agent, turn["model"], tokens, usd,
                                 "price-table" if usd is not None else "unpriced", None, (file, mid)))
    span = _span("claude", name, agent or "?", parent_agent, file, turn_events, times, model)
    return [span, *turn_events, *tools]


CODEX_CALLS = ("function_call", "custom_tool_call", "local_shell_call")
CODEX_EXIT = re.compile(r"(?:exited with code|exit code:?)\s*(-?\d+)", re.I)
CODEX_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens")


def _codex_tokens(delta: dict) -> dict:
    cached = delta.get("cached_input_tokens", 0) or 0
    return {"input": max(0, (delta.get("input_tokens", 0) or 0) - cached),
            "output": delta.get("output_tokens", 0) or 0, "cache_read": cached,
            "cache_write": delta.get("cache_write_input_tokens", 0) or 0}


def read_codex(lines: Iterable[str], file: str, agent: str | None = None,
               parent_agent: str | None = None, name: str = "codex session") -> list[Event]:
    """Codex rollout. `token_count` rows carry a cumulative `total_token_usage`: a turn's tokens are the
    difference to the previous total (all of it after a counter reset); `info: null` rows are skipped.
    `input_tokens` includes the cached share, so uncached input is the difference.
    """
    prev_total = dict.fromkeys(CODEX_FIELDS, 0)
    boundary = None
    turn_id = None
    model = None
    pending: dict[str, dict] = {}
    tools: list[Event] = []
    turn_events: list[Event] = []
    times: list[float] = []
    for row in _rows(lines):
        ts = epoch(row.get("timestamp"))
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        kind, ptype = row.get("type"), payload.get("type")
        if ts is not None:
            times.append(ts)
        if kind == "session_meta":
            agent = agent or payload.get("id")
            boundary = boundary or ts
        elif kind == "turn_context":
            model = payload.get("model") or model
            turn_id = payload.get("turn_id") or turn_id
        elif ptype == "task_started":
            boundary = ts
            turn_id = payload.get("turn_id") or turn_id
        elif kind == "response_item" and ptype in CODEX_CALLS and ts is not None:
            call_id = payload.get("call_id") or payload.get("id")
            pending[call_id] = {"name": payload.get("name") or ptype, "start": ts}
        elif kind == "response_item" and ptype and ptype.endswith("_output") and ts is not None:
            call = pending.get(payload.get("call_id"))
            if call is not None and "end" not in call:
                call["end"] = ts
                found = CODEX_EXIT.search(_result_text(payload.get("output")))
                call["exit"] = int(found.group(1)) if found else None
        elif ptype == "token_count" and isinstance(payload.get("info"), dict) and ts is not None:
            total = payload["info"].get("total_token_usage") or {}
            delta = {k: (total.get(k, 0) or 0) - prev_total[k] for k in CODEX_FIELDS}
            if any(v < 0 for v in delta.values()):
                delta = {k: total.get(k, 0) or 0 for k in CODEX_FIELDS}
            prev_total = {k: total.get(k, 0) or 0 for k in CODEX_FIELDS}
            tokens = _codex_tokens(delta)
            usd = openai_cost(model, tokens)
            turn_events.append(Event("turn", "turn", boundary if boundary is not None else ts, ts, "codex",
                                     agent or "?", parent_agent, model, tokens, usd,
                                     "price-table" if usd is not None else "unpriced", None,
                                     (file, turn_id)))
            boundary = ts
    last = max(times) if times else 0.0
    for call_id, call in pending.items():
        tools.append(Event("tool", call["name"], call["start"], call.get("end", last), "codex",
                           agent or "?", parent_agent, model, None, None, "unpriced", call.get("exit"),
                           (file, call_id)))
    span = _span("codex", name, agent or "?", parent_agent, file, turn_events, times, model)
    return [span, *turn_events, *tools]


def read_pi(lines: Iterable[str], file: str, agent: str | None = None,
            parent_agent: str | None = None, name: str = "pi session") -> list[Event]:
    """Pi session. Cost is Pi's own record (`usage.cost.total`), not repriced: a recorded 0 for a local
    model stays 0 and is labelled `pi-recorded`. A turn without a cost record is unpriced.
    """
    pending: dict[str, dict] = {}
    tools: list[Event] = []
    turn_events: list[Event] = []
    times: list[float] = []
    prev = None
    model = None
    for row in _rows(lines):
        ts = epoch(row.get("timestamp"))
        kind = row.get("type")
        if kind == "session":
            agent = agent or row.get("id")
        elif kind == "model_change":
            model = row.get("modelId") or model
        if ts is None or kind != "message":
            continue
        times.append(ts)
        message = row.get("message") or {}
        role = message.get("role")
        if role == "assistant":
            model = message.get("model") or model
            usage = message.get("usage") or {}
            cost = usage.get("cost") if isinstance(usage.get("cost"), dict) else {}
            recorded = cost.get("total")
            tokens = {"input": usage.get("input", 0) or 0, "output": usage.get("output", 0) or 0,
                      "cache_read": usage.get("cacheRead", 0) or 0,
                      "cache_write": usage.get("cacheWrite", 0) or 0}
            turn_events.append(Event("turn", "turn", prev if prev is not None else ts, ts, "pi",
                                     agent or "?", parent_agent, model, tokens,
                                     float(recorded) if recorded is not None else None,
                                     "pi-recorded" if recorded is not None else "unpriced", None,
                                     (file, row.get("id"))))
            for block in message.get("content") if isinstance(message.get("content"), list) else []:
                if isinstance(block, dict) and block.get("type") == "toolCall" and block.get("id"):
                    pending[block["id"]] = {"name": block.get("name") or "?", "start": ts}
        elif role == "toolResult":
            call = pending.get(message.get("toolCallId"))
            if call is not None and "end" not in call:
                call["end"] = ts
                call["exit"] = 1 if message.get("isError") else 0
        elif role == "bashExecution":
            code = message.get("exitCode")
            tools.append(Event("tool", "bash", ts, ts, "pi", agent or "?", parent_agent, model, None, None,
                               "unpriced", code if isinstance(code, int) else None, (file, None)))
        prev = ts
    last = max(times) if times else 0.0
    for call_id, call in pending.items():
        tools.append(Event("tool", call["name"], call["start"], call.get("end", last), "pi", agent or "?",
                           parent_agent, model, None, None, "unpriced", call.get("exit"), (file, call_id)))
    span = _span("pi", name, agent or "?", parent_agent, file, turn_events, times, model)
    return [span, *turn_events, *tools]


def read_opaque(runtime: str, file: str, start: float, end: float, agent: str | None = None,
                parent_agent: str | None = None, name: str | None = None) -> list[Event]:
    """Runtimes with no structured log (aider, vibe): one span, pointer is the file only."""
    return [Event("agent", name or f"{runtime} session", start, max(start, end), runtime, agent or file,
                  parent_agent, None, None, None, "unpriced", None, (file, None))]


def zstd_lines(path: Path) -> list[str]:
    """Decompressed lines of a `.zst` archive copy (the `zstd` CLI, as transcript_archive.py writes it)."""
    out = subprocess.run(["zstd", "-dc", "--", str(path)], capture_output=True, check=True)
    return out.stdout.decode("utf-8", "replace").splitlines()


def open_lines(path: Path) -> list[str]:
    """Lines of a plain or `.zst` transcript."""
    if path.suffix == ".zst":
        return zstd_lines(path)
    with path.open(encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()
