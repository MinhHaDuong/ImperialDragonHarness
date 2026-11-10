#!/usr/bin/env python3
"""Create verify-gate's detached gate worktree, replacing a stale same-round one.

    gate_tree.py add --repo <primary root> --tree <.../gate-<unit>-<session>-r<round>>
                     --ref <commit-ish>

A gate round that stalls (its fork ended while a check ran, ticket 1490)
records no verdict and leaves its tree behind; the relaunch under the same
session derives the same round and so the same path. When that path is
already a worktree of the repository, it is a detached checkout of a pushed
head with nothing to salvage: it is removed through
`worktree-exit-preflight.sh --removal` and recreated at `--ref`.

Refused (exit 1, nothing removed; the gate rules ESCALATE, Missing Data):
- the tree is locked, attached to a branch (a gate tree is always detached),
  or the path exists but is not a worktree of `--repo`;
- the tree's HEAD holds a commit no branch, remote or tag reaches;
- the preflight finds residue: a modified, staged or untracked file (ignored
  files are disposable, ticket 1500).
Exit 2: usage.
Prints the tree path on success.
"""

import argparse
import subprocess
import sys
from pathlib import Path

PREFLIGHT = Path(__file__).resolve().parent / "worktree-exit-preflight.sh"


def refuse(message: str) -> int:
    print(f"gate_tree: {message}", file=sys.stderr)
    return 1


def registered(repo: Path, tree: Path) -> dict | None:
    """The `git worktree list --porcelain` record of `tree`, or None."""
    out = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"],
                         capture_output=True, text=True, check=True).stdout
    want = tree.resolve()
    for block in out.split("\n\n"):
        fields = dict((line.split(" ", 1) + [""])[:2] for line in block.splitlines() if line)
        if "worktree" in fields and Path(fields["worktree"]).resolve() == want:
            return fields
    return None


def add(a: argparse.Namespace) -> int:
    record = registered(a.repo, a.tree)
    if record is None and (a.tree.exists() or a.tree.is_symlink()):
        return refuse(f"{a.tree} exists and is not a worktree of {a.repo}")
    if record is not None:
        if "locked" in record:
            return refuse(f"{a.tree} is locked ({record['locked'] or 'no reason'}); a live run may own it")
        if "detached" not in record:
            return refuse(f"{a.tree} is attached to a branch, not a detached gate tree; left in place")
        # The preflight sees uncommitted state only; a commit made on the detached
        # tree that no branch, remote or tag reaches dies with it. The registered
        # HEAD is read through the repository, so a deleted directory is checked too.
        loose = subprocess.run(["git", "-C", str(a.repo), "rev-list", "-n1", record.get("HEAD", ""),
                                "--not", "--branches", "--remotes", "--tags"],
                               capture_output=True, text=True)
        if not record.get("HEAD") or loose.returncode != 0 or loose.stdout.strip():
            sys.stderr.write(loose.stderr)
            return refuse(f"stale {a.tree} holds a commit not reachable from any "
                          f"branch, remote or tag; left in place")
        if a.tree.is_dir():
            check = subprocess.run([str(PREFLIGHT), "--removal", str(a.tree)],
                                   capture_output=True, text=True)
            if check.returncode != 0:
                sys.stderr.write(check.stderr)
                return refuse(f"stale {a.tree} holds residue; left in place")
        gone = subprocess.run(["git", "-C", str(a.repo), "worktree", "remove", str(a.tree)],
                              capture_output=True, text=True)
        if gone.returncode != 0:
            sys.stderr.write(gone.stderr)
            return refuse(f"cannot remove stale {a.tree}")
        print(f"gate_tree: replaced stale {a.tree}", file=sys.stderr)
    done = subprocess.run(["git", "-C", str(a.repo), "worktree", "add", "--detach",
                           str(a.tree), a.ref])
    if done.returncode != 0 or not a.tree.is_dir():
        return refuse(f"cannot create isolated gate worktree {a.tree}")
    print(a.tree)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add", help="create the gate tree, replacing a stale same-round one")
    p.add_argument("--repo", type=Path, required=True, help="the primary checkout")
    p.add_argument("--tree", type=Path, required=True)
    p.add_argument("--ref", required=True, help="the head to check out, detached")
    a = parser.parse_args()
    return add(a)


if __name__ == "__main__":
    raise SystemExit(main())
