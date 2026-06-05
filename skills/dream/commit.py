#!/usr/bin/env python3
"""
Commit dream consolidation results to git. Pure git ops — no LLM calls.
Scoped to the project's memory directory; never touches other files.
"""

import argparse
import subprocess
import sys
from pathlib import Path

MEMORY_BASE = Path.home() / ".claude" / "projects"
IDH_BASE = Path.home() / ".claude"


def main():
    parser = argparse.ArgumentParser(
        description="Commit or roll back a dream consolidation."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    commit_p = sub.add_parser("commit")
    commit_p.add_argument("project")
    commit_p.add_argument("n_before", type=int)
    commit_p.add_argument("n_after", type=int)

    rollback_p = sub.add_parser("rollback")
    rollback_p.add_argument("commit_hash")

    args = parser.parse_args()

    if args.cmd == "commit":
        memory_dir = MEMORY_BASE / args.project / "memory"
        harness_memory_dir = IDH_BASE / "memory"
        message = (
            f"dream: consolidate {args.project} memory ({args.n_before}→{args.n_after})"
        )
        try:
            # Stage project-level memory changes
            subprocess.run(
                ["git", "-C", str(IDH_BASE), "add", "-f", str(memory_dir)],
                check=True,
                capture_output=True,
            )
            # Stage harness-level memory changes (provenance + promotions)
            if harness_memory_dir.exists():
                subprocess.run(
                    ["git", "-C", str(IDH_BASE), "add", "-f", str(harness_memory_dir)],
                    check=True,
                    capture_output=True,
                )
            subprocess.run(
                ["git", "-C", str(IDH_BASE), "commit", "-m", message],
                check=True,
                capture_output=True,
            )
            print(f"Committed: {message}")
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e.stderr.decode()}", file=sys.stderr)
            sys.exit(1)

    elif args.cmd == "rollback":
        try:
            subprocess.run(
                ["git", "-C", str(IDH_BASE), "revert", "--no-edit", args.commit_hash],
                check=True,
                capture_output=True,
            )
            print(f"Rolled back {args.commit_hash}")
        except subprocess.CalledProcessError as e:
            print(f"Rollback failed: {e.stderr.decode()}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
