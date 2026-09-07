#!/usr/bin/env python3
"""Inventory stale IDH skills from local Claude session traces.

The report is aggregate-only: trace paths, prompts, tool inputs other than skill
names, and session identifiers never leave memory or appear in the output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

COMMAND_RE = re.compile(r"<command-name>/?([\w-]+)</command-name>")
ACTIVE_ROOTS = (
    "agents",
    "bin",
    "commands",
    "hooks",
    "rules",
    "scripts",
    "skills",
    "systemd",
)


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def skill_invocations(projects_dir: Path, cutoff: datetime) -> tuple[Counter, dict]:
    """Return aggregate skill invocations and corpus coverage metadata."""
    counts: Counter = Counter()
    files_seen = files_in_window = malformed_lines = 0
    latest_record: datetime | None = None

    if not projects_dir.is_dir():
        return counts, {
            "trace_files_seen": 0,
            "trace_files_in_window": 0,
            "malformed_lines": 0,
            "latest_record": None,
        }

    for path in projects_dir.rglob("*.jsonl"):
        files_seen += 1
        file_in_window = False
        seen_tool_ids: set[str] = set()
        try:
            lines = path.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with lines:
            for raw in lines:
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError:
                    malformed_lines += 1
                    continue
                if not isinstance(record, dict):
                    continue
                timestamp = parse_timestamp(record.get("timestamp"))
                if timestamp is None or timestamp < cutoff:
                    continue
                file_in_window = True
                latest_record = (
                    max(latest_record, timestamp) if latest_record else timestamp
                )
                message = record.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if record.get("type") == "assistant" and isinstance(content, list):
                    for block in content:
                        if (
                            not isinstance(block, dict)
                            or block.get("type") != "tool_use"
                        ):
                            continue
                        if block.get("name") != "Skill":
                            continue
                        tool_id = block.get("id")
                        if isinstance(tool_id, str) and tool_id in seen_tool_ids:
                            continue
                        if isinstance(tool_id, str):
                            seen_tool_ids.add(tool_id)
                        tool_input = block.get("input")
                        if isinstance(tool_input, dict) and isinstance(
                            tool_input.get("skill"), str
                        ):
                            counts[tool_input["skill"]] += 1
                elif record.get("type") == "user" and isinstance(content, str):
                    for match in COMMAND_RE.finditer(content):
                        counts[match.group(1)] += 1
        files_in_window += int(file_in_window)

    return counts, {
        "trace_files_seen": files_seen,
        "trace_files_in_window": files_in_window,
        "malformed_lines": malformed_lines,
        "latest_record": latest_record.isoformat() if latest_record else None,
    }


def tracked_active_files(repo: Path) -> list[Path]:
    command = [
        "git",
        "-C",
        str(repo),
        "ls-files",
        *ACTIVE_ROOTS,
        "CLAUDE.md",
        "settings.shared.json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        return []
    return [repo / line for line in result.stdout.splitlines() if line]


def active_references(repo: Path, skill: str, files: list[Path]) -> int:
    patterns = (
        re.compile(rf"skills/{re.escape(skill)}(?:/|\b)"),
        re.compile(rf"(?<![\w-])[/\$]{re.escape(skill)}(?![\w-])"),
        re.compile(
            rf"(?:skill|command)[\"']?\s*[:=]\s*[\"']{re.escape(skill)}[\"']",
            re.IGNORECASE,
        ),
    )
    own = repo / "skills" / skill
    references = 0
    for path in files:
        if own in path.parents:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        references += sum(len(pattern.findall(text)) for pattern in patterns)
    return references


def last_change(repo: Path, skill: str) -> datetime | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--format=%cI", "--", f"skills/{skill}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return parse_timestamp(result.stdout.strip()) if result.returncode == 0 else None


def build_report(repo: Path, projects_dir: Path, days: int, now: datetime) -> dict:
    cutoff = now - timedelta(days=days)
    invocations, coverage = skill_invocations(projects_dir, cutoff)
    files = tracked_active_files(repo)
    rows = []
    for skill_dir in sorted((repo / "skills").iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
            continue
        name = skill_dir.name
        used = invocations[name]
        references = active_references(repo, name, files)
        changed = last_change(repo, name)
        if used:
            disposition = "keep-used"
        elif references:
            disposition = "keep-dependency"
        elif coverage["trace_files_in_window"] == 0:
            disposition = "indeterminate-no-traces"
        elif changed is not None and changed >= cutoff:
            disposition = "indeterminate-recent"
        else:
            disposition = "candidate-remove"
        rows.append(
            {
                "skill": name,
                "invocations": used,
                "active_references": references,
                "last_change": changed.isoformat() if changed else None,
                "disposition": disposition,
            }
        )

    dispositions = Counter(row["disposition"] for row in rows)
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "window_days": days,
        "cutoff": cutoff.isoformat(),
        "privacy": "aggregate-only; no prompts, session ids, or trace paths",
        "providers_observed": ["claude"],
        "coverage": coverage,
        "summary": {"skills": len(rows), **dict(sorted(dispositions.items()))},
        "skills": rows,
    }


def default_output() -> Path:
    state_root = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_root / "imperial-dragon-harness" / "mammoth-audit.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate stale-skill audit from local traces."
    )
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument(
        "--projects-dir", type=Path, default=Path("~/.claude/projects").expanduser()
    )
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--output", type=Path, default=default_output())
    args = parser.parse_args()
    if args.days <= 0:
        parser.error("--days must be positive")

    report = build_report(
        args.repo.resolve(),
        args.projects_dir.expanduser(),
        args.days,
        datetime.now(timezone.utc),
    )
    args.output = args.output.expanduser()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    candidates = report["summary"].get("candidate-remove", 0)
    print(
        f"mammoth-audit: {report['summary']['skills']} skills, {candidates} removal candidates; {args.output}"
    )


if __name__ == "__main__":
    main()
