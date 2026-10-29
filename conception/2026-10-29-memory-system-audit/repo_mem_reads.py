#!/usr/bin/env python3
"""Count Claude Code sessions in harness projects that read repo memory.

Arms: maintenance (session invokes hoard/roar/lair/dream skill) vs working.
Channels: Read tool file_path; Bash command strings. Main sessions only
(top-level *.jsonl); subagents counted separately.
"""

import json
import re
import sys
import glob
import os
import collections

ROOT = os.path.expanduser("~/.claude/projects")
dirs = [
    d
    for d in glob.glob(ROOT + "/*")
    if "-agents" in os.path.basename(d) and "vibe" not in d
]
PAT = {
    "index": re.compile(r"memory/MEMORY\.md"),
    "topics": re.compile(r"memory/topics/"),
    "journal": re.compile(r"memory/journal/"),
}
MAINT = re.compile(
    r'"(?:skill|command)"\s*:\s*"(?:hoard|roar|lair|dream|brood)"|<command-name>/?(?:hoard|roar|lair|dream|brood)<'
)


def scan(path):
    hits = collections.Counter()
    maint = False
    first = None
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                if (
                    b"memory/" not in raw
                    and b"hoard" not in raw
                    and b"roar" not in raw
                    and b"lair" not in raw
                    and b'"timestamp"' not in raw
                ):
                    continue
                line = raw.decode("utf-8", "replace")
                m = re.search(r'"timestamp"\s*:\s*"([0-9T:\-]+)', line)
                if m:
                    first = first or m.group(1)
                if MAINT.search(line):
                    maint = True
                if b"memory/" not in raw:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if obj.get("type") != "assistant" or not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict) or c.get("type") != "tool_use":
                        continue
                    inp = c.get("input") or {}
                    name = c.get("name")
                    target = (
                        inp.get("file_path")
                        if name == "Read"
                        else (inp.get("command") if name == "Bash" else None)
                    )
                    if not target:
                        continue
                    for k, p in PAT.items():
                        if p.search(target):
                            hits[(name, k)] += 1
    except OSError:
        pass
    return hits, maint, first


since = sys.argv[1] if len(sys.argv) > 1 else "2026-10-02"
res = {
    "main": collections.defaultdict(lambda: collections.Counter()),
    "sub": collections.defaultdict(lambda: collections.Counter()),
}
n = {"main": collections.Counter(), "sub": collections.Counter()}
for d in dirs:
    for f in glob.glob(d + "/*.jsonl") + glob.glob(d + "/*/subagents/*.jsonl"):
        kind = "sub" if "/subagents/" in f else "main"
        hits, maint, first = scan(f)
        if not first or first < since:
            continue
        arm = "maintenance" if maint else "working"
        n[kind][arm] += 1
        for (tool, k), v in hits.items():
            res[kind][arm][(tool, k)] += 1  # sessions with >=1 hit (per tool,kind)
        if any(k == "topics" and tool == "Read" for (tool, k) in hits) or any(
            k == "index" and tool == "Read" for (tool, k) in hits
        ):
            res[kind][arm][("any-Read", "index|topics")] += 1
for kind in ("main", "sub"):
    for arm in ("maintenance", "working"):
        print(
            kind, arm, "sessions:", n[kind][arm], dict(sorted(res[kind][arm].items()))
        )
