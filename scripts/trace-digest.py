#!/usr/bin/env python3
"""Per-trace digest for LLM open-coding — ticket 0240, trace-doctor phase 2b.

Compresses one session JSONL trace into a compact, privacy-safe digest a
cheap-model reader can narrate: per-turn token deltas, tool-call names,
compaction/clear boundaries, and subagent spawn points. NO trace content
crosses into the digest — no user prompts, no assistant text, no command
arguments (Bash keeps its first word only), no agent prompts. File paths
are kept: they are structural markers already committed in the census.

Long traces are coalesced: consecutive low-signal turns merge into range
rows until the digest fits --max-tokens; notable turns (compact/clear,
spawns, cache_read jumps, first/last) always stay standalone.

Token accounting follows the 0236 rule: usage counted ONCE per unique
message.id; <synthetic> records are not turns. Zero LLM/API calls.
"""

import argparse
import importlib.util
import json
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger("trace-digest")

# Reuse the census module (dedupe conventions, timestamp parsing).
_TS_SPEC = importlib.util.spec_from_file_location(
    "trace_stats", Path(__file__).resolve().parent / "trace-stats.py"
)
ts = importlib.util.module_from_spec(_TS_SPEC)
_TS_SPEC.loader.exec_module(ts)

SPAWN_TOOLS = {"Task", "Agent"}
PATH_TOOLS = {"Read", "Edit", "Write", "NotebookEdit"}
# A turn whose cache_read grows by more than this factor over the previous
# turn is notable — context just jumped.
JUMP_FACTOR = 1.5


def estimate_tokens(text: str) -> int:
    """Cheap upper-ish estimate: 4 chars per token."""
    return len(text) // 4


def _tool_label(name: str, tool_input: dict) -> str:
    """Privacy-safe label: tool name + structural marker only."""
    if name == "Bash":
        first_word = str(tool_input.get("command", "")).split()[:1]
        return f"Bash({first_word[0]})" if first_word else "Bash"
    if name in PATH_TOOLS and tool_input.get("file_path"):
        return f"{name}({tool_input['file_path']})"
    if name == "Skill" and tool_input.get("skill"):
        return f"Skill({tool_input['skill']})"
    if name in SPAWN_TOOLS:
        kind = tool_input.get("subagent_type") or "general-purpose"
        return f"SPAWN {kind}"
    return name


def parse_turns(path: Path) -> dict:
    """Parse one trace into an ordered list of turn/boundary events."""
    events: list[dict] = []
    seen_ids: set[str] = set()
    seen_tool_ids: set[str] = set()
    totals = dict.fromkeys(ts.USAGE_KEYS, 0)
    models: dict[str, int] = {}
    pending_result_bytes = 0

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

            if rec.get("type") == "system" and rec.get("subtype") == "compact_boundary":
                meta = rec.get("compactMetadata") or {}
                events.append(
                    {
                        "kind": "compact",
                        "trigger": meta.get("trigger", "?"),
                        "pre": meta.get("preTokens", 0),
                        "post": meta.get("postTokens", 0),
                    }
                )
                continue

            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")

            if rec.get("type") == "assistant":
                model = msg.get("model") or ""
                msg_id = msg.get("id")
                usage = msg.get("usage")
                turn = None
                if (
                    msg_id
                    and msg_id not in seen_ids
                    and isinstance(usage, dict)
                    and model != "<synthetic>"
                ):
                    seen_ids.add(msg_id)
                    models[model] = models.get(model, 0) + 1
                    for k in ts.USAGE_KEYS:
                        totals[k] += usage.get(k, 0) or 0
                    turn = {
                        "kind": "turn",
                        "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
                        "cache_write": usage.get("cache_creation_input_tokens", 0) or 0,
                        "output": usage.get("output_tokens", 0) or 0,
                        "tools": [],
                    }
                    events.append(turn)
                if isinstance(content, list):
                    # Tool blocks may sit on later rows of the same message:
                    # attach them to the last turn event.
                    last_turn = next(
                        (e for e in reversed(events) if e["kind"] == "turn"), None
                    )
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        block_id = block.get("id")
                        if block_id in seen_tool_ids:
                            continue
                        if block_id:
                            seen_tool_ids.add(block_id)
                        if last_turn is not None:
                            last_turn["tools"].append(
                                _tool_label(block.get("name", "?"), block.get("input") or {})
                            )
            elif rec.get("type") == "user":
                if isinstance(content, str) and re.search(
                    r"<command-name>/?clear</command-name>\s*\n", content
                ):
                    events.append({"kind": "clear"})
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            try:
                                pending_result_bytes = len(json.dumps(block.get("content", "")))
                            except (TypeError, ValueError):
                                pending_result_bytes = 0
                            last_turn = next(
                                (e for e in reversed(events) if e["kind"] == "turn"), None
                            )
                            if last_turn is not None:
                                last_turn["result_bytes"] = (
                                    last_turn.get("result_bytes", 0) + pending_result_bytes
                                )

    return {"events": events, "totals": totals, "models": models}


def _is_notable(i: int, turns: list[dict]) -> bool:
    if i == 0 or i == len(turns) - 1:
        return True
    t = turns[i]
    if any(lbl.startswith("SPAWN") or lbl.startswith("Skill(") for lbl in t["tools"]):
        return True
    prev = turns[i - 1]["cache_read"] or 1
    return t["cache_read"] / prev > JUMP_FACTOR


def _fmt_turn(i: int, t: dict) -> str:
    tools = ",".join(t["tools"]) if t["tools"] else "-"
    rb = f" res={t['result_bytes']:,}B" if t.get("result_bytes") else ""
    return f"T{i + 1} cr={t['cache_read']:,} cw={t['cache_write']:,} o={t['output']:,}{rb} | {tools}"


def _fmt_range(lo: int, hi: int, turns: list[dict]) -> str:
    chunk = turns[lo : hi + 1]
    from collections import Counter

    names = Counter(lbl.split("(")[0] for t in chunk for lbl in t["tools"])
    hist = ",".join(f"{n}x{c}" for n, c in names.most_common(6)) or "-"
    avg_cr = sum(t["cache_read"] for t in chunk) // len(chunk)
    out = sum(t["output"] for t in chunk)
    return f"T{lo + 1}-T{hi + 1} ({len(chunk)} turns) cr~{avg_cr:,}/turn o={out:,} | {hist}"


def render(parsed: dict, source: str, max_tokens: int) -> str:
    events = parsed["events"]
    turns = [e for e in events if e["kind"] == "turn"]
    totals = parsed["totals"]
    header = [
        f"# Trace digest: {source}",
        f"turns: {len(turns)}",
        f"models: {json.dumps(parsed['models'], sort_keys=True)}",
        f"fresh_input: {totals['input_tokens']:,}  output: {totals['output_tokens']:,}",
        f"cache_read: {totals['cache_read_input_tokens']:,}  "
        f"cache_write: {totals['cache_creation_input_tokens']:,}",
        "",
        "## Trajectory (cr=cache_read, cw=cache_write, o=output per turn)",
    ]

    # Build the event line list at decreasing granularity until it fits.
    for group in (1, 4, 10, 25, 60, 150, 400):
        lines: list[str] = []
        ti = -1  # index into turns
        i = 0
        while i < len(events):
            e = events[i]
            if e["kind"] == "compact":
                lines.append(
                    f"== COMPACT ({e['trigger']}) {e['pre']:,} -> {e['post']:,} =="
                )
                i += 1
                continue
            if e["kind"] == "clear":
                lines.append("== CLEAR ==")
                i += 1
                continue
            ti += 1
            if group == 1 or _is_notable(ti, turns):
                lines.append(_fmt_turn(ti, turns[ti]))
                i += 1
                continue
            # Coalesce a run of non-notable turns (no boundaries between).
            lo = ti
            while (
                i + 1 < len(events)
                and events[i + 1]["kind"] == "turn"
                and not _is_notable(ti + 1, turns)
                and ti - lo + 1 < group
            ):
                i += 1
                ti += 1
            lines.append(_fmt_range(lo, ti, turns) if ti > lo else _fmt_turn(lo, turns[lo]))
            i += 1
        text = "\n".join(header + lines) + "\n"
        if estimate_tokens(text) <= max_tokens:
            return text
    # Last resort: header only (always fits any sane budget).
    return "\n".join(header + ["(trajectory omitted: trace too large for budget)"]) + "\n"


def digest_trace(path: Path, max_tokens: int = 2000, source: str | None = None) -> str:
    return render(parse_turns(path), source or path.name, max_tokens)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Digest session traces into compact open-coding inputs."
    )
    parser.add_argument(
        "--trace",
        type=Path,
        action="append",
        required=True,
        help="Trace JSONL path (repeatable)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write one <session-id>.digest.md per trace here (default: stdout)",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=2000, help="Digest size budget (default 2000)"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    failures = 0
    for trace in args.trace:
        try:
            text = digest_trace(trace, args.max_tokens)
        except OSError as e:
            log.error("unreadable %s: %s", trace, e)
            failures += 1
            continue
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            out = args.output_dir / f"{trace.stem}.digest.md"
            out.write_text(text, encoding="utf-8")
            log.info("wrote %s (%d est. tokens)", out, estimate_tokens(text))
        else:
            sys.stdout.write(text)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
