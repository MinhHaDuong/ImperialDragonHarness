#!/usr/bin/env python3
"""Count Codex or Pi sessions that load the harness AGENTS.md and read repo memory.

Usage: codex_mem.py <sessions-dir> <since YYYY-MM-DD>

A session counts when its transcript contains the harness AGENTS.md
("Project memory boundary"). It "reads" when a tool call's payload names
memory/MEMORY.md or memory/topics/. "maint" is a keyword heuristic on user
turns (hoard, roar, lair, brood). Audit of 2026-10-29.
"""

import collections
import datetime
import glob
import json
import os
import re
import sys

MEM = re.compile(r"memory/(MEMORY\.md|topics/)")
MAINT = re.compile(r"\b(hoard|roar|lair|brood)\b")
CALL_TYPES = ("function_call", "custom_tool_call", "local_shell_call")


def scan(path):
    harness = read = maint = False
    calls = 0
    with open(path, errors="replace") as fh:
        for line in fh:
            if "Project memory boundary" in line:
                harness = True
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            payload = obj.get("payload") or obj.get("message") or {}
            if not isinstance(payload, dict):
                continue
            text = json.dumps(payload)
            is_call = payload.get("type") in CALL_TYPES or (
                payload.get("role") == "assistant" and "toolCall" in text
            )
            if is_call:
                calls += 1
                if MEM.search(text):
                    read = True
            if (
                payload.get("role") == "user"
                and MAINT.search(text[:4000])
                and "Project memory boundary" not in text
            ):
                maint = True
    return harness, read, maint, calls


def main():
    base = os.path.expanduser(sys.argv[1])
    since = datetime.datetime.fromisoformat(sys.argv[2]).timestamp()
    counts = collections.Counter()
    for path in glob.glob(base + "/**/*.jsonl", recursive=True):
        if os.path.getmtime(path) < since:
            continue
        harness, read, maint, calls = scan(path)
        if not harness:
            continue
        key = (
            "maint" if maint else "work",
            "read" if read else "noread",
            "hascalls" if calls else "nocalls",
        )
        counts[key] += 1
    for key, value in sorted(counts.items()):
        print(key, value)


if __name__ == "__main__":
    main()
