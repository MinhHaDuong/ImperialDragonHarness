#!/usr/bin/env python3
"""Harness usage census: scan every Claude Code session log and count real use
of skills, rules, scripts, guards, agents and hooks.

Streaming regex scan (no full JSON parse) -- the logs are 4 GB.
Output: one JSON blob of raw counters, for the report pass to aggregate.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TS = re.compile(rb'"timestamp":"(\d{4})-(\d\d)-(\d\d)T')

ROOT = Path.home() / ".claude"


def inventory(root: Path):
    skills = sorted(p.name for p in (root / "skills").iterdir() if p.is_dir())
    scripts = sorted(p.name for p in (root / "scripts").iterdir() if p.is_file())
    rules = sorted(str(p.relative_to(root / "rules")) for p in (root / "rules").rglob("*.md"))
    commands = sorted(p.stem for p in (root / "commands").glob("*.md"))
    agents = sorted(p.stem for p in (root / "agents").glob("*.md"))
    return skills, scripts, rules, commands, agents


SKILLS, SCRIPTS, RULES, COMMANDS, AGENTS = inventory(ROOT)

RE_SKILL = re.compile(rb'"name":\s*"Skill"\s*,\s*"input":\s*\{[^}]{0,200}?"skill":\s*"([A-Za-z0-9_-]+)"')
RE_CMD = re.compile(rb'<command-name>/?([A-Za-z0-9_-]+)</command-name>')
RE_AGENT = re.compile(rb'"subagent_type":\s*"([A-Za-z0-9_.-]+)"')
RE_RULEINJ = re.compile(rb'-----\s+((?:rules|prose|doctype|lang|format)/[A-Za-z0-9_.-]+\.md)\s+-----')
RE_TOOLNAME = re.compile(rb'"type":\s*"tool_use"\s*,\s*"id":\s*"[^"]+"\s*,\s*"name":\s*"([A-Za-z0-9_-]+)"')
RE_BASH = re.compile(rb'"name":\s*"Bash"\s*,\s*"input":\s*\{\s*"command":\s*"((?:[^"\\]|\\.){0,4000})"')
RE_PATH = re.compile(rb'"file_path":\s*"([^"]{0,300})"')

SCRIPT_RE = re.compile(
    rb'(?:^|[/\s"\'`(=])('
    + b'|'.join(re.escape(s.encode()) for s in sorted(SCRIPTS, key=len, reverse=True))
    + rb')(?:$|[\s"\'`);&|])'
)
RULE_READ_RE = re.compile(rb'rules/((?:[a-z]+/)?[A-Za-z0-9_.-]+\.md)')
SKILL_FILE_RE = re.compile(rb'skills/([A-Za-z0-9_-]+)/')

RMF = b"BLOCKED: " + b"rm -" + b"rf"
GUARD_KEYS = {
    "guard-cd-primary-repo.sh": b"targets the PRIMARY repo",
    "guard-commit-on-main.sh": b"BLOCKED: committing directly to",
    "guard-destructive-bash.sh": RMF,
    "guard-enterworktree-parked-cwd.sh": b"session base cwd is parked",
    "guard-no-push.sh": b"git push is not allowed in automated mode",
    "guard-worktree-identity.sh": b"worktree identity mismatch",
    "pretooluse-worktree-path-guard.sh": b"Worktree path guard",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=str(ROOT / "projects"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    def dd():
        return defaultdict(Counter)

    skill_tool = dd()
    slash = dd()
    agent = dd()
    ruleinj = dd()
    script_use = dd()
    rule_read = dd()
    skill_read = dd()
    toolmix = dd()
    guard_fire = dd()
    skill_by_project = defaultdict(Counter)
    script_by_project = defaultdict(Counter)
    days = Counter()
    sessions_by_day = defaultdict(set)
    project_days = defaultdict(Counter)
    files_seen = 0
    bytes_seen = 0

    for dirpath, _dirs, fnames in os.walk(a.projects):
        proj = Path(dirpath).name
        for fn in fnames:
            if not fn.endswith(".jsonl"):
                continue
            p = os.path.join(dirpath, fn)
            files_seen += 1
            try:
                bytes_seen += os.path.getsize(p)
            except OSError:
                pass
            sid = fn[:-6]
            cur_date = "unknown"
            try:
                fh = open(p, "rb")
            except OSError:
                continue
            with fh:
                for line in fh:
                    m = TS.search(line)
                    if m:
                        cur_date = f"{m.group(1).decode()}-{m.group(2).decode()}-{m.group(3).decode()}"
                    d = cur_date
                    days[d] += 1
                    sessions_by_day[d].add(sid)
                    project_days[proj][d] += 1

                    if b'"tool_use"' in line:
                        for mm in RE_TOOLNAME.finditer(line):
                            toolmix[mm.group(1).decode()][d] += 1
                        if b'"Skill"' in line:
                            for mm in RE_SKILL.finditer(line):
                                n = mm.group(1).decode()
                                skill_tool[n][d] += 1
                                skill_by_project[n][proj] += 1
                        if b'"subagent_type"' in line:
                            for mm in RE_AGENT.finditer(line):
                                agent[mm.group(1).decode()][d] += 1
                        if b'"Bash"' in line:
                            for mm in RE_BASH.finditer(line):
                                cmd = mm.group(1)
                                for sm in SCRIPT_RE.finditer(cmd):
                                    n = sm.group(1).decode()
                                    script_use[n][d] += 1
                                    script_by_project[n][proj] += 1
                        if b'file_path' in line:
                            for pm in RE_PATH.finditer(line):
                                pth = pm.group(1)
                                for rm in RULE_READ_RE.finditer(pth):
                                    rule_read[rm.group(1).decode()][d] += 1
                                for km in SKILL_FILE_RE.finditer(pth):
                                    skill_read[km.group(1).decode()][d] += 1

                    if b'<command-name>' in line:
                        for mm in RE_CMD.finditer(line):
                            slash[mm.group(1).decode()][d] += 1

                    if b'----- ' in line:
                        for mm in RE_RULEINJ.finditer(line):
                            ruleinj[mm.group(1).decode()][d] += 1

                    for gname, pat in GUARD_KEYS.items():
                        if pat in line:
                            guard_fire[gname][d] += 1

    def pack(x):
        return {k: dict(v) for k, v in x.items()}

    out = {
        "meta": {
            "files": files_seen,
            "bytes": bytes_seen,
            "inventory": {
                "skills": SKILLS,
                "scripts": SCRIPTS,
                "rules": RULES,
                "commands": COMMANDS,
                "agents": AGENTS,
            },
        },
        "days": dict(days),
        "sessions_by_day": {k: len(v) for k, v in sessions_by_day.items()},
        "skill_tool": pack(skill_tool),
        "slash": pack(slash),
        "agent": pack(agent),
        "rule_injection": pack(ruleinj),
        "rule_read": pack(rule_read),
        "skill_read": pack(skill_read),
        "script_use": pack(script_use),
        "tool_mix": pack(toolmix),
        "guard_fire": pack(guard_fire),
        "skill_by_project": {k: dict(v) for k, v in skill_by_project.items()},
        "script_by_project": {k: dict(v) for k, v in script_by_project.items()},
        "project_days": {k: dict(v) for k, v in project_days.items()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f)
    print(f"files={files_seen} bytes={bytes_seen / 1e9:.2f}G -> {a.out}", file=sys.stderr)


main()
