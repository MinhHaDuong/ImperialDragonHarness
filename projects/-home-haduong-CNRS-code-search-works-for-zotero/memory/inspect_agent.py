#!/usr/bin/env python3
"""Summarise a subagent JSONL transcript by tool-call shape only.

Prints no message content: just timestamps, tool names and short argument
fingerprints, so a coordinator can see whether a lane is looping without
pulling its output into context.
"""
import json
import sys
from collections import Counter

path = sys.argv[1]
tail = int(sys.argv[2]) if len(sys.argv) > 2 else 40

rows = []
with open(path, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                inp = block.get("input") or {}
                fp = inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("description") or ""
                rows.append((d.get("timestamp", "")[11:19], block.get("name"), str(fp)[:110]))

print(f"total tool calls: {len(rows)}")
print("\ntop tools:")
for name, n in Counter(r[1] for r in rows).most_common(12):
    print(f"  {n:4d}  {name}")

print(f"\nlast {tail} calls:")
for ts, name, fp in rows[-tail:]:
    print(f"  {ts}  {name:12s}  {fp}")

print("\nmost repeated fingerprints (loop tell):")
for fp, n in Counter(r[2] for r in rows).most_common(8):
    if n > 1:
        print(f"  {n:4d}x  {fp[:100]}")
