#!/usr/bin/env python3
"""Enumerate merged PRs since a sentinel SHA as celebration records (ticket 0331).

Roar's telemetry step logs one celebration per merged PR instead of a single
aggregate blob. This script enumerates the merge commits in ``<since-sha>..HEAD``
on the current branch and emits, per merge, one JSON object per line carrying the
fields roar's ``log-celebration`` expects (that helper stamps ``ts``/``date``):

    {"project": str, "branch": str|null, "commits": int,
     "files_changed": int, "ticket": int|null}

Branch is parsed from the GitHub-shaped merge subject; ticket is recovered by
scanning the merge's second-parent commit range for the erg-pr-merge close
commit, NOT from the branch name (real branch names such as
``worktree-agent-a31bf6655c104744e`` carry misleading digits).

An empty range prints nothing and exits 0. The sentinel-missing / non-ancestor
guards live in roar's SKILL.md prose, not here.
"""

import argparse
import json
import os
import re
import subprocess
import sys

# GitHub-shaped merge subject: "Merge pull request #123 from owner/branch-name".
PR_SUBJECT_RE = re.compile(r"^Merge pull request #(\d+) from [^/]+/(.+)$")

# erg-pr-merge writes its close commit as exactly
#   ticket(<id>[, <id>...]): close and archive — PR #<n>
# (skills/merge/erg-pr-merge ~line 228; CLOSED_LIST joins IDs with ", ").
# Anchor on the whole "close and archive … PR #<n>" template, NOT just the
# ticket(...) prefix: ordinary ticket-FILING commits also start "ticket(NNNN):",
# so a PR with no close commit (Ticket: none, non-erg merge) would otherwise
# mis-attribute a filing commit's id. If the close format changes, update this.
CLOSE_COMMIT_RE = re.compile(
    r"^ticket\((\d+)(?:,\s*\d+)*\): close and archive — PR #\d+$"
)


def git(args: list[str], cwd: str | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def repo_root() -> str:
    # Resolve at call time — never at import (worktree-safe; see memory
    # feedback_module_level_git_paths).
    return git(["rev-parse", "--show-toplevel"]).strip()


def merge_commits(since_sha: str, root: str) -> list[str]:
    out = git(
        [
            "log",
            "--merges",
            "--first-parent",
            "--reverse",
            "--format=%H",
            f"{since_sha}..HEAD",
        ],
        cwd=root,
    )
    return [line for line in out.splitlines() if line.strip()]


def merge_meta(sha: str, root: str) -> tuple[list[str], str]:
    """Return (parent SHAs, subject) for a merge commit."""
    out = git(["show", "-s", "--format=%P%n%s", sha], cwd=root).splitlines()
    parents = out[0].split() if out else []
    subject = out[1] if len(out) > 1 else ""
    return parents, subject


def branch_from_subject(subject: str) -> str | None:
    m = PR_SUBJECT_RE.match(subject)
    return m.group(2) if m else None


def ticket_from_range(parent1: str, parent2: str, root: str) -> int | None:
    subjects = git(
        ["log", "--format=%s", f"{parent1}..{parent2}"], cwd=root
    ).splitlines()
    for subject in subjects:
        m = CLOSE_COMMIT_RE.match(subject.strip())
        if m:
            return int(m.group(1))
    return None


def commits_in_range(parent1: str, parent2: str, root: str) -> int:
    return int(
        git(["rev-list", "--count", f"{parent1}..{parent2}"], cwd=root).strip()
    )


def files_changed(parent1: str, parent2: str, root: str) -> int:
    # Three-dot (merge-base relative) so a batched session's intervening PRs,
    # which advanced parent1 but are absent from parent2, do not leak in as
    # phantom changes. This is the PR's own diff — what GitHub's "Files changed"
    # and a raid's immediate per-PR roar record. --numstat yields one line per
    # changed file (locale-independent; no summary-line parse to localize).
    out = git(["diff", "--numstat", f"{parent1}...{parent2}"], cwd=root)
    return sum(1 for ln in out.splitlines() if ln.strip())


def build_records(since_sha: str, project: str, root: str) -> list[dict]:
    records = []
    for sha in merge_commits(since_sha, root):
        parents, subject = merge_meta(sha, root)
        if len(parents) < 2:
            # --merges guarantees >= 2 parents; skip defensively otherwise.
            continue
        p1, p2 = parents[0], parents[1]
        records.append(
            {
                "project": project,
                "branch": branch_from_subject(subject),
                "commits": commits_in_range(p1, p2, root),
                "files_changed": files_changed(p1, p2, root),
                "ticket": ticket_from_range(p1, p2, root),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit one celebration JSON record per merged PR since a SHA."
    )
    parser.add_argument(
        "since_sha",
        help="sentinel SHA; merges in <since_sha>..HEAD are enumerated",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="project name for the record (default: repo directory name)",
    )
    args = parser.parse_args()

    root = repo_root()
    project = args.project or os.path.basename(root)
    for record in build_records(args.since_sha, project, root):
        print(json.dumps(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
