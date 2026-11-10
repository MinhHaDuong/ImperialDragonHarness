#!/usr/bin/env python3
"""Register a worktree's .tmp/ scratch as git-ignored in the common info/exclude.

`register WORKTREE` appends `/.tmp/` and `/.claude/worktrees/` once (ticket 1119).
Removal needs no check of its own: `.tmp/` is ignored scratch, deleted with its
worktree like any other ignored file (ticket 1500)."""

import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys


PREFIX = "worktree-tmp-guard:"


class Blocked(Exception):
    pass


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError as exc:
        raise Blocked(f"could not run git {args[0]}: {exc}") from exc
    if check and result.returncode:
        raise Blocked(f"could not inspect Git {args[0]} (exit {result.returncode})")
    return result


def common_dir(repo: Path) -> Path:
    value = run_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    if not value:
        raise Blocked("could not resolve common Git metadata")
    return Path(value)


def register_tmp_exclude(worktree_arg: Path) -> int:
    worktree = worktree_arg.resolve(strict=True)
    root = Path(run_git(worktree, "rev-parse", "--show-toplevel").stdout.strip()).resolve(strict=True)
    if worktree != root:
        raise Blocked("candidate path is not a worktree root")
    exclude = common_dir(root) / "info" / "exclude"
    try:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.seek(0)
            lines = stream.read().splitlines()
            missing = [rule for rule in ("/.tmp/", "/.claude/worktrees/") if rule not in lines]
            if missing:
                stream.seek(0, os.SEEK_END)
                stream.write("\n" + "\n".join(missing) + "\n")
                stream.flush()
    except OSError as exc:
        raise Blocked(f"could not register exclude rules in common info/exclude: {exc}") from exc
    print(f"{PREFIX} registered /.tmp/ and /.claude/worktrees/ in {exclude}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("register",))
    parser.add_argument("worktree", type=Path)
    args = parser.parse_args()
    try:
        return register_tmp_exclude(args.worktree)
    except Blocked as exc:
        print(f"{PREFIX} BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
