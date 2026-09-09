#!/usr/bin/env python3
"""Skill-doctor survey — mine git history for recurring failure patterns.

Emits JSON: {window, patterns}
  window: {since, until, days}
  patterns: [{signature, frequency, severity, score, evidence, affected_skill, candidate_patch}]

Patterns are ranked by score = frequency × severity_weight.
Severity weights: high=3, medium=2, low=1.

Six further lenses once read the nightbeat supervisor's journal and its run
logs: budget raises, dirty trees, watermark redetection, unclosed umbrellas,
max-turns exhaustion and crash recovery. Ticket 0882 removed the nightbeat
block, so nothing writes either source any more and those six could only report
"no pattern" forever — an all-clear indistinguishable from a blind spot. They
were removed with their source rather than left to return empty; git history
holds them if the pipeline ever returns.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
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

    # Collect evidence
    repair_commits = _git_log_grep("repair:", since)
    ticket_commits = _git_log_grep("ticket(", since)

    # Run all clusterers
    patterns = []
    for clusterer in (
        lambda: _cluster_ticket_line_format(repair_commits + ticket_commits),
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
