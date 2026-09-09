#!/usr/bin/env python3
"""Third pass: file access to rules/ and skills/ split by tool (consult vs edit).

A `Read` of rules/git.md is consultation; an `Edit` of it is harness development.
Conflating them makes a rule that only ever gets rewritten look well used.
"""
import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.home() / ".claude"
TS = re.compile(rb'"timestamp":"(\d{4}-\d\d-\d\d)T')
TU = re.compile(
    rb'"type":\s*"tool_use"\s*,\s*"id":\s*"[^"]+"\s*,\s*"name":\s*"(Read|Edit|Write|NotebookEdit|MultiEdit)"\s*,'
    rb'\s*"input":\s*\{(?:[^{}]|\{[^{}]*\}){0,600}?"file_path":\s*"([^"]{0,300})"'
)
RULE = re.compile(r"rules/((?:[a-z]+/)?[A-Za-z0-9_.-]+\.md)$")
SKILL = re.compile(r"skills/([A-Za-z0-9_-]+)/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=str(ROOT / "projects"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rules = defaultdict(Counter)  # rule -> {"Read": n, "Edit": n}
    skills = defaultdict(Counter)
    rule_days = defaultdict(lambda: defaultdict(set))
    skill_days = defaultdict(lambda: defaultdict(set))

    for dirpath, _d, fnames in os.walk(a.projects):
        for fn in fnames:
            if not fn.endswith(".jsonl"):
                continue
            cur = "unknown"
            try:
                fh = open(os.path.join(dirpath, fn), "rb")
            except OSError:
                continue
            with fh:
                for line in fh:
                    m = TS.search(line)
                    if m:
                        cur = m.group(1).decode()
                    if b"file_path" not in line:
                        continue
                    for tm in TU.finditer(line):
                        tool = tm.group(1).decode()
                        path = tm.group(2).decode("unicode_escape", "replace")
                        kind = "read" if tool == "Read" else "write"
                        rm = RULE.search(path)
                        if rm:
                            rules[rm.group(1)][kind] += 1
                            rule_days[rm.group(1)][kind].add(cur)
                        sm = SKILL.search(path)
                        if sm:
                            skills[sm.group(1)][kind] += 1
                            skill_days[sm.group(1)][kind].add(cur)

    out = {
        "rules": {
            k: {**dict(v), "read_days": len(rule_days[k]["read"]), "write_days": len(rule_days[k]["write"])}
            for k, v in rules.items()
        },
        "skills": {
            k: {**dict(v), "read_days": len(skill_days[k]["read"]), "write_days": len(skill_days[k]["write"])}
            for k, v in skills.items()
        },
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("ok", len(rules), len(skills))


main()
