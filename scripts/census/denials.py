#!/usr/bin/env python3
"""Join every guard denial back to the command it blocked, and to the reason the
guard gave.

"The guard fired 711 times" says nothing about whether it fired on a hazard or on
a false positive. The join is on the tool_result's tool_use_id, which is the only
key that ties a refusal to the command that provoked it.
"""
import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

TS = re.compile(r'"timestamp":"(\d{4}-\d\d-\d\d)T')
HOOKERR = re.compile(r"PreToolUse:[A-Za-z|]* ?hook error: \[([^\]]*)\]: (.*)")
NATIVE = re.compile(r"too complex to verify|Edit the worktree copy of this file")


def guard_name(bracket: str) -> str:
    m = re.search(r"([a-z0-9_.-]+\.(?:sh|py))", bracket)
    return m.group(1) if m else bracket[:40]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-samples", type=int, default=250)
    a = ap.parse_args()

    counts = Counter()
    reasons = defaultdict(Counter)
    samples = defaultdict(list)
    joined = Counter()

    for dirpath, _d, fnames in os.walk(a.projects):
        for fn in fnames:
            if not fn.endswith(".jsonl"):
                continue
            cmds: dict[str, str] = {}
            try:
                fh = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace")
            except OSError:
                continue
            cur = "unknown"
            with fh:
                for line in fh:
                    m = TS.search(line)
                    if m:
                        cur = m.group(1)
                    if '"tool_use"' in line and '"Bash"' in line:
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        for c in (rec.get("message") or {}).get("content") or []:
                            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                                cmd = (c.get("input") or {}).get("command")
                                if isinstance(cmd, str):
                                    cmds[c.get("id", "")] = cmd
                        continue
                    if '"is_error":true' not in line.replace(" ", "") and "hook error" not in line:
                        if not NATIVE.search(line):
                            continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = (rec.get("message") or {}).get("content")
                    if not isinstance(content, list):
                        continue
                    for c in content:
                        if not isinstance(c, dict) or c.get("type") != "tool_result":
                            continue
                        txt = c.get("content")
                        if not isinstance(txt, str):
                            continue
                        hm = HOOKERR.search(txt)
                        if hm:
                            name = guard_name(hm.group(1))
                            reason = hm.group(2).strip()[:110]
                        elif NATIVE.search(txt):
                            name = "native-worktree-gate"
                            reason = "platform refusal (complex command / primary-checkout path)"
                        else:
                            continue
                        counts[name] += 1
                        reasons[name][reason] += 1
                        cmd = cmds.get(c.get("tool_use_id", ""), "")
                        if cmd:
                            joined[name] += 1
                            if len(samples[name]) < a.max_samples:
                                samples[name].append({"day": cur, "cmd": cmd[:500]})

    out = {
        "counts": dict(counts),
        "joined": dict(joined),
        "reasons": {k: dict(v.most_common(12)) for k, v in reasons.items()},
        "samples": dict(samples),
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("ok", dict(counts))


main()
