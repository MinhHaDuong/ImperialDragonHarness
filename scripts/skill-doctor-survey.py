#!/usr/bin/env python3
"""Skill-doctor survey — mine journals, logs, and git history for recurring failure patterns.

Emits JSON: {window, patterns}
  window: {since, until, days}
  patterns: [{signature, frequency, severity, score, evidence, affected_skill, candidate_patch}]

Patterns are ranked by score = frequency × severity_weight.
Severity weights: high=3, medium=2, low=1.
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


def _resolve_harness_dir() -> Path:
    """Resolve the real harness directory, following worktree symlinks."""
    script_dir = Path(__file__).resolve().parent.parent
    env = os.environ.get("HARNESS_DIR")
    if env:
        return Path(env)
    git_file = script_dir / ".git"
    if git_file.is_file():
        gitdir_line = git_file.read_text().strip()
        if gitdir_line.startswith("gitdir:"):
            worktree_git = Path(gitdir_line.split(":", 1)[1].strip()).resolve()
            commondir = worktree_git / "commondir"
            if commondir.is_file():
                real_gitdir = (worktree_git / commondir.read_text().strip()).resolve()
                return real_gitdir.parent
    return script_dir


HARNESS_DIR = _resolve_harness_dir()


def _parse_ts(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _read_jsonl(path: Path, since: datetime | None = None) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since is not None:
            ts = _parse_ts(obj.get("ts", ""))
            if ts is not None and ts < since:
                continue
        rows.append(obj)
    return rows


def _git_log_grep(pattern: str, since: datetime) -> list[str]:
    try:
        r = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--oneline",
                f"--since={since.isoformat()}",
                f"--grep={pattern}",
            ],
            capture_output=True,
            text=True,
            cwd=HARNESS_DIR,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return []
    return r.stdout.strip().splitlines() if r.returncode == 0 else []


def _scan_nightbeat_logs(since: datetime) -> list[str]:
    """Extract failure signature lines from nightbeat logs."""
    log_dir = HARNESS_DIR / "logs" / "nightbeat"
    if not log_dir.exists():
        return []
    lines = []
    for logfile in sorted(log_dir.glob("*.log")):
        stem = logfile.stem[:15]
        try:
            file_dt = datetime.strptime(stem, "%Y%m%dT%H%M%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if file_dt < since:
            continue
        try:
            content = logfile.read_text(errors="replace")
        except OSError:
            continue
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("{"):
                continue
            low = stripped.lower()
            if any(
                kw in low
                for kw in (
                    "aborted",
                    "error",
                    "fail",
                    "denied",
                    "budget",
                    "timeout",
                    "max-turns",
                    "outcome=",
                )
            ):
                lines.append(stripped)
    return lines


def _cluster_budget_raises(
    journal: list[dict], repair_commits: list[str]
) -> dict | None:
    """Detect repeated budget raises for the same project+phase."""
    raises: list[dict] = []
    for entry in journal:
        action = entry.get("action", "")
        note = entry.get("note", "")
        if action == "repair" and "budget" in note.lower():
            raises.append(entry)
    seen_msgs: set[str] = set()
    for commit in repair_commits:
        if "raise" in commit.lower() and "budget" in commit.lower():
            # Deduplicate: same commit message from different branches
            msg = commit.split(" ", 1)[1] if " " in commit else commit
            if msg not in seen_msgs:
                seen_msgs.add(msg)
                raises.append({"source": "git", "line": commit})

    if len(raises) < 2:
        return None

    by_project: dict[str, int] = Counter()
    for r in raises:
        proj = r.get("project", "unknown")
        by_project[proj] += 1

    return {
        "signature": "budget-cap-repeated-raises",
        "frequency": len(raises),
        "severity": "medium",
        "score": len(raises) * 2,
        "evidence": [r.get("note") or r.get("line", "") for r in raises[:6]],
        "affected_skill": "nightbeat-supervisor",
        "candidate_patch": (
            "After 3 consecutive budget raises for the same project+phase "
            "within 7 days, escalate to a ticket instead of raising again. "
            "Log a warning when a raise would exceed 1.5x the module-level constant."
        ),
    }


def _cluster_dirty_tree(log_lines: list[str]) -> dict | None:
    """Detect dirty working tree blocking checkout."""
    dirty = [
        ln
        for ln in log_lines
        if "cannot checkout" in ln
        and ("modifications locales" in ln or "local changes" in ln.lower())
    ]
    if len(dirty) < 2:
        return None

    files_mentioned: set[str] = set()
    for ln in dirty:
        for m in re.findall(r"\t(\S+)", ln):
            files_mentioned.add(m)

    return {
        "signature": "dirty-tree-blocks-checkout",
        "frequency": len(dirty),
        "severity": "medium",
        "score": len(dirty) * 2,
        "evidence": [ln[:200] for ln in dirty[:4]],
        "dirty_files": sorted(files_mentioned)[:10],
        "affected_skill": "beat.py (_sync_origin_main)",
        "candidate_patch": (
            "In _sync_origin_main(), check `git status --porcelain` first. "
            "If dirty, log the dirty files and abort with error code "
            "'aborted-dirty-tree' so the supervisor can open a ticket."
        ),
    }


def _cluster_watermark_redetection(journal: list[dict]) -> dict | None:
    """Detect watermark/journal issues causing re-detection loops."""
    redetect = []
    for entry in journal:
        note = entry.get("note", "").lower()
        if any(kw in note for kw in ("already repaired", "re-detect", "watermark")):
            redetect.append(entry)

    if len(redetect) < 2:
        return None

    return {
        "signature": "watermark-redetection-loop",
        "frequency": len(redetect),
        "severity": "high",
        "score": len(redetect) * 3,
        "evidence": [r.get("note", "")[:200] for r in redetect[:4]],
        "affected_skill": "nightbeat-supervisor-survey.py",
        "candidate_patch": (
            "Add a startup assertion to the survey script: verify the canonical "
            "journal path exists and no non-canonical duplicate exists independently. "
            "Fail loud if both exist."
        ),
    }


def _cluster_umbrella_not_closed(
    journal: list[dict], log_lines: list[str]
) -> dict | None:
    """Detect umbrella tickets staying open after children complete."""
    umbrella_events = []
    for entry in journal:
        note = entry.get("note", "").lower()
        if "umbrella" in note and (
            "open" in note or "closed" in note or "never closed" in note
        ):
            umbrella_events.append(entry)
    for ln in log_lines:
        if "umbrella" in ln.lower() and "closed" in ln.lower():
            umbrella_events.append({"source": "log", "note": ln[:200]})

    if len(umbrella_events) < 2:
        return None

    return {
        "signature": "umbrella-not-auto-closed",
        "frequency": len(umbrella_events),
        "severity": "medium",
        "score": len(umbrella_events) * 2,
        "evidence": [e.get("note", "")[:200] for e in umbrella_events[:4]],
        "affected_skill": "pick-ticket",
        "candidate_patch": (
            "In pick-ticket step 3: if a ticket has Blocks: entries, check "
            "whether all referenced tickets are closed. If yes, auto-close "
            "as already-done."
        ),
    }


def _cluster_ticket_line_format(repair_commits: list[str]) -> dict | None:
    """Detect plain Ticket: vs **Ticket:** format mismatches."""
    ticket_line_issues = [
        c
        for c in repair_commits
        if "ticket:" in c.lower() and ("tolerate" in c.lower() or "plain" in c.lower())
    ]
    if len(ticket_line_issues) < 1:
        return None

    freq = len(ticket_line_issues)
    return {
        "signature": "ticket-line-format-mismatch",
        "frequency": freq,
        "severity": "high",
        "score": freq * 3,
        "evidence": ticket_line_issues[:4],
        "affected_skill": "merge (erg-pr-merge)",
        "candidate_patch": (
            "Loosen the grep in erg-pr-merge to accept Ticket:, **Ticket:**, "
            "and **Ticket**: at line start (case-insensitive). If no ticket line "
            "is found at all, exit non-zero."
        ),
    }


def _cluster_max_turns(journal: list[dict], log_lines: list[str]) -> dict | None:
    """Detect max-turns exhaustion events."""
    events = []
    for entry in journal:
        note = entry.get("note", "").lower()
        if "max-turns" in note or "max_turns" in note:
            events.append(entry)
    for ln in log_lines:
        if "max-turns" in ln.lower() or "max_turns" in ln.lower():
            events.append({"source": "log", "note": ln[:200]})

    if len(events) < 2:
        return None

    return {
        "signature": "max-turns-exhaustion",
        "frequency": len(events),
        "severity": "medium",
        "score": len(events) * 2,
        "evidence": [e.get("note", "")[:200] for e in events[:4]],
        "affected_skill": "beat.py (pick-ticket/raid)",
        "candidate_patch": (
            "Per-project max_turns_pick_ticket already landed (ticket 0115). "
            "Monitor for recurrence; if still hitting, consider dynamic turn "
            "allocation based on ticket complexity."
        ),
    }


def _cluster_crash_recovery(log_lines: list[str]) -> dict | None:
    """Detect crash recovery events."""
    crashes = [ln for ln in log_lines if "crash recovery" in ln.lower()]
    if len(crashes) < 2:
        return None
    return {
        "signature": "beat-crash-recovery",
        "frequency": len(crashes),
        "severity": "low",
        "score": len(crashes) * 1,
        "evidence": [ln[:200] for ln in crashes[:4]],
        "affected_skill": "beat.py",
        "candidate_patch": (
            "Investigate crash root causes from log context. "
            "Add structured crash reason to beat-outcomes.jsonl."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Look-back window in days (default: 30)",
    )
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=2,
        help="Minimum occurrences to report a pattern (default: 2)",
    )
    args = parser.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    until = datetime.now(timezone.utc)

    # Collect evidence from all sources
    journal_path = HARNESS_DIR / "logs" / "nightbeat-supervisor-journal.jsonl"
    journal_alt = HARNESS_DIR / "nightbeat-supervisor-journal.jsonl"
    journal = _read_jsonl(journal_path, since)
    if journal_alt.exists() and journal_alt != journal_path:
        journal.extend(_read_jsonl(journal_alt, since))

    repair_commits = _git_log_grep("repair:", since)
    ticket_commits = _git_log_grep("ticket(", since)
    log_lines = _scan_nightbeat_logs(since)

    # Run all clusterers
    patterns = []
    for clusterer in (
        lambda: _cluster_budget_raises(journal, repair_commits),
        lambda: _cluster_dirty_tree(log_lines),
        lambda: _cluster_watermark_redetection(journal),
        lambda: _cluster_umbrella_not_closed(journal, log_lines),
        lambda: _cluster_ticket_line_format(repair_commits + ticket_commits),
        lambda: _cluster_max_turns(journal, log_lines),
        lambda: _cluster_crash_recovery(log_lines),
    ):
        result = clusterer()
        if result and result["frequency"] >= args.min_frequency:
            patterns.append(result)

    patterns.sort(key=lambda p: p["score"], reverse=True)

    print(
        json.dumps(
            {
                "window": {
                    "since": since.isoformat(),
                    "until": until.isoformat(),
                    "days": args.days,
                },
                "pattern_count": len(patterns),
                "patterns": patterns,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
