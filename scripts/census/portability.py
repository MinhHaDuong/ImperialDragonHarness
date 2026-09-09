#!/usr/bin/env python3
"""Size the adapter surface: how much of each skill depends on a Claude Code
primitive that no other agent runtime provides.

Counting the mentions is crude but it is the quantity that decides how much of a
skill has to be rewritten rather than copied, which is the question the port asks.
"""
import argparse
import json
import re
from pathlib import Path

CC_ONLY = {
    "Skill tool": r"\bSkill\(|Skill tool",
    "Agent/subagent": r"\bAgent\(|subagent_type|isolation:\s*[\"']worktree|Task\(",
    "Workflow": r"\bWorkflow\(|workflow-authoring",
    "worktree tools": r"EnterWorktree|ExitWorktree",
    "hooks": r"PreToolUse|PostToolUse|SessionStart|SessionEnd|UserPromptSubmit|hookSpecificOutput",
    "messaging": r"SendMessage|ListAgents|TaskStop|TaskOutput|Monitor\(",
    "slash/frontmatter": r"^\s*(?:allowed-tools|argument-hint|disable-model-invocation|context):",
    "settings.json": r"settings\.json|permissions\.allow|effortLevel",
    "model tokens": r"\b(?:opus|sonnet|haiku|fable)\b",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path.home() / ".claude"))
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    R = Path(a.root)
    rep = json.load(open(a.report))
    used = {s["skill"]: s["total"] for s in rep["skills"]}

    rows = []
    for d in sorted((R / "skills").iterdir()):
        sk = d / "SKILL.md"
        if not sk.exists():
            continue
        txt = "\n".join(p.read_text(errors="replace") for p in d.rglob("*") if p.is_file() and p.suffix in {".md", ".sh", ".py"})
        hits = {k: len(re.findall(v, txt, re.M)) for k, v in CC_ONLY.items()}
        rows.append((d.name, used.get(d.name, 0), sum(hits.values()), len(txt), hits))

    rows.sort(key=lambda r: -r[1])
    print(f"{'skill':<26}{'usage':>6}{'CC-deps':>9}{'chars':>8}  principales dependances")
    for n, u, tot, ln, hits in rows:
        top = ", ".join(f"{k}:{v}" for k, v in sorted(hits.items(), key=lambda kv: -kv[1]) if v)[:74]
        print(f"{n:<26}{u:>6}{tot:>9}{ln:>8}  {top}")
    print()
    live = [r for r in rows if r[1] > 0]
    print(f"skills vivantes: {len(live)}  dependances CC cumulees: {sum(r[2] for r in live)}")
    dead = [r for r in rows if r[1] == 0]
    print(f"skills mortes:   {len(dead)}  dependances CC cumulees: {sum(r[2] for r in dead)}")


main()
