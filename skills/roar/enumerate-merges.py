#!/usr/bin/env python3
"""Enumerate merged PRs since a sentinel SHA as celebration records (ticket 0331).

Roar's telemetry step logs one celebration per merged PR instead of a single
aggregate blob. This script enumerates the merge commits in
``<since-sha>..<until>`` (``--until`` defaults to ``HEAD``) and emits, per merge,
one JSON object per line carrying the fields roar's ``log-celebration`` expects
(that helper stamps ``ts``/``date``):

    {"project": str, "branch": str|null, "commits": int,
     "files_changed": int, "ticket": int|null}

Branch is parsed from the GitHub-shaped merge subject; ticket is recovered by
scanning the merge's second-parent commit range for the erg-pr-merge close
commit, NOT from the branch name (real branch names such as
``worktree-agent-a31bf6655c104744e`` carry misleading digits).

An empty range prints nothing and exits 0. The sentinel-missing / non-ancestor
guards live in roar's SKILL.md prose, not here.

``--until`` exists because /roar normally runs from the worktree of the branch
just merged, and that worktree sits on the branch tip — BELOW the merge commit.
Enumerating to a hard-coded ``HEAD`` there misses the very merge being
celebrated, silently (ticket 0500).

Octopus merges (3+ parents) are skipped with a stderr note: the per-PR fields
are defined for a two-sided PR merge, so an N-way merge is reported rather than
silently undercounted. The forge's PR-merge path is always 2-parent; octopus
merges only occur on the standalone/no-forge CLI path.
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


def merge_commits(since_sha: str, until: str, root: str) -> list[str]:
    out = git(
        [
            "log",
            "--merges",
            "--first-parent",
            "--reverse",
            "--format=%H",
            f"{since_sha}..{until}",
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


def commits_and_ticket(parent1: str, parent2: str, root: str) -> tuple[int, int | None]:
    """Return (commit count, ticket id) for a two-dot range in one git call.

    The subject list `git log` returns while scanning for the close commit
    already has one line per commit, so its length is the commit count — no
    separate `rev-list --count` spawn needed.
    """
    subjects = git(
        ["log", "--format=%s", f"{parent1}..{parent2}"], cwd=root
    ).splitlines()
    ticket = None
    for subject in subjects:
        m = CLOSE_COMMIT_RE.match(subject.strip())
        if m:
            ticket = int(m.group(1))
            break
    return len(subjects), ticket


def files_changed(parent1: str, parent2: str, root: str) -> int:
    # Three-dot (merge-base relative) so a batched session's intervening PRs,
    # which advanced parent1 but are absent from parent2, do not leak in as
    # phantom changes. This is the PR's own diff — what GitHub's "Files changed"
    # and a raid's immediate per-PR roar record. --numstat yields one line per
    # changed file (locale-independent; no summary-line parse to localize).
    out = git(["diff", "--numstat", f"{parent1}...{parent2}"], cwd=root)
    return sum(1 for ln in out.splitlines() if ln.strip())


def build_records(since_sha: str, until: str, project: str, root: str) -> list[dict]:
    records = []
    for sha in merge_commits(since_sha, until, root):
        parents, subject = merge_meta(sha, root)
        if len(parents) < 2:
            # --merges guarantees >= 2 parents; skip defensively otherwise.
            continue
        if len(parents) > 2:
            # Octopus merge: the per-PR fields (branch, commits, files, ticket)
            # are defined for a two-sided PR merge, so an N-way merge cannot be
            # reduced to one without silently dropping parents 3..N. Skip it
            # visibly rather than undercount.
            print(f"skipping octopus merge {sha} ({len(parents)} parents)",
                  file=sys.stderr)
            continue
        p1, p2 = parents[0], parents[1]
        commits, ticket = commits_and_ticket(p1, p2, root)
        records.append(
            {
                "project": project,
                "branch": branch_from_subject(subject),
                "commits": commits,
                "files_changed": files_changed(p1, p2, root),
                "ticket": ticket,
            }
        )
    return records


# Options whose VALUE may legitimately begin with a dash. Only these are glued;
# an unknown option keeps argparse's own error handling.
VALUE_OPTIONS = ("--project", "--until")
KNOWN_OPTIONS = VALUE_OPTIONS + ("-h", "--help")


def normalize_argv(argv: list[str]) -> list[str]:
    """Rewrite ``--opt <-value>`` as ``--opt=<-value>`` (ticket 0500).

    Every directory under ``~/.claude/projects/`` begins with a dash
    (``-home-haduong--claude``, …), and argparse reads such a value as the start
    of another option, aborting with a usage dump. Roar's step 2 swallows that
    exit and degrades to one aggregate record for a whole session, so the
    normalization lives here rather than in each call site's memory: the
    ``--opt=value`` spelling is the only form argparse accepts for a
    leading-dash value.

    A token the parser already knows is never a value: ``--project --until``
    means the value was omitted, and gluing it hides that behind a satisfied
    option and a stray positional. Leaving the pair alone lets argparse report
    the missing value itself.
    """
    out: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--":  # everything after the separator is a value already
            out.extend(argv[i:])
            break
        if (
            token in VALUE_OPTIONS
            and i + 1 < len(argv)
            and argv[i + 1].startswith("-")
            and argv[i + 1] not in KNOWN_OPTIONS
        ):
            out.append(f"{token}={argv[i + 1]}")
            i += 2
            continue
        out.append(token)
        i += 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit one celebration JSON record per merged PR since a SHA."
    )
    parser.add_argument(
        "since_sha",
        help="sentinel SHA; merges in <since_sha>..<until> are enumerated",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="project name for the record (default: repo directory name)",
    )
    parser.add_argument(
        "--until",
        default="HEAD",
        help=(
            "terminal reference (default: HEAD). A roar run from the merged "
            "branch's worktree must pass origin/main: the worktree sits below "
            "the merge commit and HEAD would enumerate short"
        ),
    )
    args = parser.parse_args(normalize_argv(sys.argv[1:]))

    root = repo_root()
    project = args.project or os.path.basename(root)
    for record in build_records(args.since_sha, args.until, project, root):
        print(json.dumps(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
