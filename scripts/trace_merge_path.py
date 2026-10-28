#!/usr/bin/env python3
"""Trace the review and gate path before each merge, from session traces.

For every main session that merged something since a date, list in order the
events that decide whether the merge was gated: skill loads (hunt, gaze,
verify-gate, merge, raid), agent launches whose prompt names gaze or
verify-gate, `merge-gate.py tier` answers, and merge commands (`gh pr merge`,
`raid_land.py`). The session's subagent traces are folded in, so a raid that
gates inside a subagent still counts as gated.

Each merging session is classed by what precedes its last merge:
- gated: a verify-gate load or launch;
- bookkeeping: no gate, but a tier answer of bookkeeping or unchanged;
- no gate seen: neither. These are the sessions to read by hand (an author
  override, an ungated repository, or a skipped gate).

It also counts verify-gate loads whose arguments carry no `repo=`: the gate
stops on those by design, so each is a wasted turn.

Only Claude Code's layout is read (`<root>/<project>/<session>.jsonl`, its
subagents under `<session>/subagents/`). Output names a session by its first
eight characters and its project directory; no prompt or command text is
printed. An unreadable root prints "not checked", never an all-clear.
"""

import argparse
import json
import re
import sys
from pathlib import Path

WATCHED_SKILLS = {"hunt", "gaze", "verify-gate", "merge", "raid"}
COMMAND_RE = re.compile(r"<command-name>/?([\w:-]+)</command-name>")
# A merge command at the start of a shell statement, not one quoted in a grep
# or a commit message.
MERGE_RE = re.compile(
    r"(?:^|[;&|(]\s*|&&\s*)(?:gh pr merge(?![^\n;&|]*--disable-auto)|python3?\s+\S*raid_land\.py)",
    re.MULTILINE,
)
TIER_RE = re.compile(r"merge-gate\.py\"?\s+tier\b")
TIER_ANSWER_RE = re.compile(r"^\s*(bookkeeping|full|unchanged)\b", re.MULTILINE)


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(_text(part.get("text", "")) for part in content if isinstance(part, dict))
    return ""


def session_events(path: Path) -> list[tuple[str, str]]:
    """(timestamp, event) pairs of one trace file, in file order."""
    events: list[tuple[str, str]] = []
    pending_tier: dict[str, str] = {}
    stamp = ""
    with path.open(errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            # A row without a timestamp keeps the last one seen, so sorting
            # with the subagent events never moves it to the front.
            stamp = row.get("timestamp") or stamp
            content = (row.get("message") or {}).get("content")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                kind = block.get("type")
                if kind == "text" and row.get("type") == "user":
                    for name in COMMAND_RE.findall(block.get("text", "")):
                        if name in WATCHED_SKILLS:
                            events.append((stamp, f"S:{name}"))
                elif kind == "tool_use":
                    tool, given = block.get("name"), block.get("input") or {}
                    if tool == "Skill" and given.get("skill") in WATCHED_SKILLS:
                        skill = given["skill"]
                        if skill == "verify-gate" and "repo=" not in str(given.get("args", "")):
                            events.append((stamp, "S:verify-gate!norepo"))
                        else:
                            events.append((stamp, f"S:{skill}"))
                    elif tool in ("Agent", "Task"):
                        prompt = f"{given.get('prompt', '')} {given.get('description', '')}".lower()
                        if "verify-gate" in prompt:
                            events.append((stamp, "A:verify-gate"))
                        elif "gaze" in prompt:
                            events.append((stamp, "A:gaze"))
                    elif tool == "Bash":
                        command = str(given.get("command", ""))
                        if TIER_RE.search(command):
                            pending_tier[block.get("id", "")] = stamp
                        if MERGE_RE.search(command):
                            events.append((stamp, "MERGE"))
                elif kind == "tool_result" and block.get("tool_use_id") in pending_tier:
                    found = TIER_ANSWER_RE.search(_text(block.get("content")))
                    answer = found.group(1) if found else "unread"
                    events.append((pending_tier.pop(block["tool_use_id"]), f"TIER:{answer}"))
    return events


def classify(events: list[tuple[str, str]]) -> str | None:
    """The class of a session's last merge, or None when it merged nothing."""
    names = [name for _, name in events]
    if "MERGE" not in names:
        return None
    before = names[: len(names) - 1 - names[::-1].index("MERGE")]
    if any(name.startswith(("S:verify-gate", "A:verify-gate")) and not name.endswith("!norepo")
           for name in before):
        return "gated"
    if any(name in ("TIER:bookkeeping", "TIER:unchanged") for name in before):
        return "bookkeeping"
    return "no gate seen"


def survey(root: Path, since: str) -> dict:
    sessions = []
    for trace in sorted(root.glob("*/*.jsonl")):
        events = session_events(trace)
        if not events or events[0][0][:10] < since:
            continue
        for sub in sorted((trace.parent / trace.stem / "subagents").glob("*.jsonl")):
            events.extend(event for event in session_events(sub)
                          if event[1].startswith(("S:verify-gate", "A:verify-gate")))
        events.sort(key=lambda event: event[0])
        verdict = classify(events)
        if verdict is None:
            continue
        sessions.append({
            "date": events[0][0][:10],
            "session": trace.stem[:8],
            "project": trace.parent.name,
            "class": verdict,
            "path": " ".join(name for _, name in events),
        })
    launches = sum(s["path"].split().count(n) for s in sessions
                   for n in ("S:verify-gate", "S:verify-gate!norepo"))
    norepo = sum(s["path"].split().count("S:verify-gate!norepo") for s in sessions)
    return {"since": since, "sessions": sessions, "gate_loads": launches, "gate_loads_norepo": norepo}


def render(report: dict) -> str:
    sessions = report["sessions"]
    counts = {name: sum(s["class"] == name for s in sessions)
              for name in ("gated", "bookkeeping", "no gate seen")}
    lines = [
        f"trace-merge-path: {len(sessions)} merging session(s) since {report['since']}: "
        + ", ".join(f"{name} {count}" for name, count in counts.items()),
        f"verify-gate loads: {report['gate_loads']}, without repo=: {report['gate_loads_norepo']}",
    ]
    unexplained = [s for s in sessions if s["class"] == "no gate seen"]
    if unexplained:
        lines.append("no gate seen (read these):")
        lines.extend(f"  {s['date']} {s['session']} {s['project']}: {s['path']}" for s in unexplained)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", required=True, help="first session date, YYYY-MM-DD")
    parser.add_argument("--root", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"trace-merge-path: not checked: {args.root} unreadable")
        return 2
    report = survey(args.root, args.since)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
