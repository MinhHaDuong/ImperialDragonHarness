#!/usr/bin/env python3
"""Fail closed unless a checkout contains the requested PR's nonempty diff.

The Skill tool may inherit a session cwd instead of its invoking Agent's cwd.
Call this with an explicit worktree before and after a built-in review.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(*argv: str, cwd: Path | None = None) -> str:
    try:
        return subprocess.run(argv, check=True, capture_output=True, text=True,
                              timeout=20, cwd=cwd).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"command failed: {' '.join(argv[:3])}: {exc}") from exc


def anchor(pr: str, worktree: Path) -> None:
    if not worktree.is_absolute() or not worktree.is_dir():
        raise ValueError("worktree must be an existing absolute directory")
    metadata = json.loads(run("gh", "pr", "view", pr, "--json", "headRefOid,baseRefName",
                              cwd=worktree))
    expected = metadata["headRefOid"]
    base = metadata["baseRefName"]
    if not expected or not base:
        raise ValueError("PR head or base is unavailable")
    root = run("git", "-C", str(worktree), "rev-parse", "--show-toplevel")
    if Path(root).resolve() != worktree.resolve():
        raise ValueError(f"worktree is not the repository root: {worktree}")
    head = run("git", "-C", str(worktree), "rev-parse", "HEAD")
    if head != expected:
        raise ValueError(f"wrong HEAD for PR #{pr}: worktree={head} PR={expected}")
    base_ref = f"refs/remotes/origin/{base}"
    run("git", "-C", str(worktree), "rev-parse", "--verify", base_ref)
    changed = run("git", "-C", str(worktree), "diff", "--name-only", "--no-renames",
                  f"{base_ref}...HEAD")
    if not changed:
        raise ValueError(f"empty diff for PR #{pr} at {head}")
    print(f"REVIEW-ANCHOR: PR #{pr} HEAD {head} base {base_ref}")
    print(changed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", help="PR number")
    parser.add_argument("--worktree", required=True, type=Path)
    args = parser.parse_args()
    try:
        anchor(args.pr, args.worktree)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REVIEW-ANCHOR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
