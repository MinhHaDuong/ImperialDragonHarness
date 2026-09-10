#!/usr/bin/env python3
"""Does the resident memory index earn its bytes?

The index sits in the system prompt of every session of its project. Recall
relevance is decided by each body's own `description:`, so the one thing
residency buys is *unprompted awareness* — a session opening a memory body
because the index told it the body exists, when nothing in the conversation
would have surfaced it.

That event has a signature: a **working** session reads a memory body. A
session that runs `/dream`, `/roar`, `/lair` or `/memory` reads bodies because
maintaining them is its job, and counting those would measure the memory
system's own housekeeping rather than its use. So sessions are split, and the
maintenance arm doubles as the positive control: if the probe cannot see reads
there, it cannot see them anywhere, and a zero in the working arm would mean
nothing.

Three arms, printed together, because a bare count of the third is unreadable:

  maintenance   sessions invoking a memory skill        (positive control)
  working       every other session                     (the measurement)
  writes        Edit/Write on a body, either kind        (housekeeping volume)

A body reached through a shell call (`cat`, `sed`, `grep`) carries no
`file_path`, so a tool-use scan alone undercounts every arm. Bash command
strings are therefore scanned too and reported as their own channel rather than
merged: a shell read is usually the agent inspecting memory as a file, and a
`Read` is usually the agent consulting it as memory, and collapsing the two
would flatter whichever conclusion one wanted.

Residual blind spot, stated rather than papered over: `Grep` carries a pattern
rather than a path, so a body found by content search is invisible here. It
measured 0 occurrences naming a body slug, so the residue is small.
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict

TS = re.compile(rb'"timestamp":"(\d{4}-\d\d-\d\d)T')
TU = re.compile(
    rb'"type":\s*"tool_use"\s*,\s*"id":\s*"[^"]+"\s*,\s*"name":\s*"(Read|Edit|Write|MultiEdit)"\s*,'
    rb'\s*"input":\s*\{(?:[^{}]|\{[^{}]*\}){0,600}?"file_path":\s*"([^"]{0,300})"'
)
MEM = re.compile(r"memory/([A-Za-z0-9_.-]+\.md)$")
SKILL = re.compile(rb'"skill":\s*"(dream|roar|lair|memory)"')
CMD = re.compile(rb"<command-name>/?(dream|roar|lair|memory)</command-name>")
BASH = re.compile(rb'"name":\s*"Bash"\s*,\s*"input":\s*\{\s*"command":\s*"((?:[^"\\]|\\.){0,4000})"')
BASH_MEM = re.compile(r"memory/((?:feedback|project|reference|user)[A-Za-z0-9_.-]*\.md)")


def scan_file(path: str) -> dict:
    """One session: is it maintenance, and which memory bodies did it touch?"""
    maintenance = False
    reads: Counter = Counter()
    writes: Counter = Counter()
    shell: Counter = Counter()
    index_reads = 0
    day = "unknown"
    try:
        fh = open(path, "rb")
    except OSError:
        return {}
    with fh:
        for line in fh:
            m = TS.search(line)
            if m:
                day = m.group(1).decode()
            if SKILL.search(line) or CMD.search(line):
                maintenance = True
            if b"memory/" not in line:
                continue
            for bm in BASH.finditer(line):
                cmd = bm.group(1).decode("unicode_escape", "replace")
                shell.update(set(BASH_MEM.findall(cmd)))
            for tm in TU.finditer(line):
                tool = tm.group(1).decode()
                mm = MEM.search(tm.group(2).decode("unicode_escape", "replace"))
                if not mm:
                    continue
                name = mm.group(1)
                if name == "MEMORY.md":
                    if tool == "Read":
                        index_reads += 1
                    continue
                (reads if tool == "Read" else writes)[name] += 1
    return {
        "maintenance": maintenance,
        "reads": reads,
        "writes": writes,
        "shell": shell,
        "index_reads": index_reads,
        "day": day,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projects", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    arms = {
        "maintenance": {
            "sessions": 0, "sessions_with_read": 0, "reads": Counter(),
            "sessions_with_shell": 0, "shell": Counter(),
        },
        "working": {
            "sessions": 0, "sessions_with_read": 0, "reads": Counter(),
            "sessions_with_shell": 0, "shell": Counter(),
        },
    }
    writes = Counter()
    index_read_sessions = 0
    days = defaultdict(set)
    total = 0
    # The harness repo is where memory files are themselves the work: a session
    # there touching one is editing the memory system, not consulting it. Kept
    # apart so the measurement is not read off its own subject matter.
    harness = {"sessions": 0, "touched": 0}
    consumer = {"sessions": 0, "touched": 0}

    for dirpath, _dirs, fnames in os.walk(a.projects):
        for fn in fnames:
            if not fn.endswith(".jsonl"):
                continue
            r = scan_file(os.path.join(dirpath, fn))
            if not r:
                continue
            total += 1
            slug = os.path.basename(dirpath)
            bucket = harness if slug.startswith("-home-haduong--claude") else consumer
            bucket["sessions"] += 1
            if (r["reads"] or r["shell"]) and not r["maintenance"]:
                bucket["touched"] += 1
            arm = arms["maintenance" if r["maintenance"] else "working"]
            arm["sessions"] += 1
            key = "maintenance" if r["maintenance"] else "working"
            if r["reads"]:
                arm["sessions_with_read"] += 1
                arm["reads"].update(r["reads"])
                days[key].add(r["day"])
            if r["shell"]:
                arm["sessions_with_shell"] += 1
                arm["shell"].update(r["shell"])
                days[key].add(r["day"])
            writes.update(r["writes"])
            if r["index_reads"]:
                index_read_sessions += 1

    out = {
        "sessions_scanned": total,
        "arms": {
            k: {
                "sessions": v["sessions"],
                "sessions_with_body_read": v["sessions_with_read"],
                "body_reads": sum(v["reads"].values()),
                "sessions_with_shell_read": v["sessions_with_shell"],
                "shell_reads": sum(v["shell"].values()),
                "sessions_touching_a_body": v["sessions_with_read"] + v["sessions_with_shell"],
                "distinct_bodies": len(set(v["reads"]) | set(v["shell"])),
                "active_days": len(days[k]),
                "top": (v["reads"] + v["shell"]).most_common(15),
            }
            for k, v in arms.items()
        },
        "body_writes": sum(writes.values()),
        "sessions_reading_the_index_itself": index_read_sessions,
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)

    w, m = out["arms"]["working"], out["arms"]["maintenance"]
    print(f"sessions scanned: {total}")
    for label, arm in (("maintenance (positive control)", m), ("working (the measurement)", w)):
        pct = 100 * arm["sessions_touching_a_body"] / arm["sessions"] if arm["sessions"] else 0
        print(f"  {label}")
        print(f"    sessions                 : {arm['sessions']}")
        print(f"    touched a body           : {arm['sessions_touching_a_body']}  ({pct:.2f}%)")
        print(f"      via Read               : {arm['sessions_with_body_read']} sessions, {arm['body_reads']} reads")
        print(f"      via shell              : {arm['sessions_with_shell_read']} sessions, {arm['shell_reads']} reads")
        print(f"    distinct bodies touched  : {arm['distinct_bodies']}")
    print(f"  body writes (housekeeping)  : {out['body_writes']}")
    print(f"  sessions reading MEMORY.md as a file: {index_read_sessions}")


main()
