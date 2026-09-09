#!/usr/bin/env python3
"""Human-typed slash commands from history.jsonl (longer horizon than the JSONL logs)."""
import argparse
import datetime
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RE = re.compile(r"(?:^|\s)/([A-Za-z0-9_-]+)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=str(Path.home() / ".claude" / "history.jsonl"))
    ap.add_argument("--start", default="2026-05-09")
    ap.add_argument("--end", default="2026-09-09")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    per_cmd = defaultdict(Counter)  # cmd -> month -> n
    per_cmd_days = defaultdict(set)
    per_cmd_proj = defaultdict(set)
    months = Counter()
    prompts = 0
    for line in open(a.history):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = e.get("timestamp")
        if not isinstance(ts, (int, float)):
            continue
        dt = datetime.datetime.fromtimestamp(ts / 1000 if ts > 1e11 else ts)
        day = dt.strftime("%Y-%m-%d")
        if not (a.start <= day <= a.end):
            continue
        prompts += 1
        months[day[:7]] += 1
        disp = e.get("display") or ""
        proj = e.get("project") or ""
        seen = set()
        for m in RE.finditer(disp):
            c = m.group(1)
            if c in seen:
                continue
            seen.add(c)
            per_cmd[c][day[:7]] += 1
            per_cmd_days[c].add(day)
            per_cmd_proj[c].add(proj)

    out = {
        "window": [a.start, a.end],
        "prompts": prompts,
        "months": dict(sorted(months.items())),
        "commands": {
            c: {
                "total": sum(v.values()),
                "by_month": dict(sorted(v.items())),
                "days": len(per_cmd_days[c]),
                "projects": len(per_cmd_proj[c]),
                "first": min(per_cmd_days[c]),
                "last": max(per_cmd_days[c]),
            }
            for c, v in sorted(per_cmd.items(), key=lambda kv: -sum(kv[1].values()))
        },
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("prompts", prompts, "commands", len(per_cmd))


main()
