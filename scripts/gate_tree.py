#!/usr/bin/env python3
"""Create verify-gate's detached gate worktree, replacing a stale same-round one.

    gate_tree.py add --repo <primary root> --tree <.../gate-<unit>-<session>-r<round>>
                     --ref <commit-ish> --session <uuid> --round <n> [--gate-state <file>]

A gate round that stalls (its fork ended while a check ran, ticket 1490)
records no verdict and leaves its tree behind; the relaunch under the same
session derives the same round and so the same path. When that path is
already a worktree of the repository, it is a detached checkout of a pushed
head with nothing to salvage: it is removed through
`worktree-exit-preflight.sh --removal --ignored-ok` and recreated at `--ref`.

Refused (exit 1, nothing removed; the gate rules ESCALATE, Missing Data):
- `--gate-state` (the JSON `review_notes.py gate` printed) records a verdict
  for this session and round: that round is ruled, its tree is not stale;
- the tree is locked, or the path exists but is not a worktree of `--repo`;
- the preflight finds residue other than regenerable or git-ignored output.
Exit 2: usage, including a tree whose name does not start with `gate-`.
Prints the tree path on success.
"""

import argparse
import json
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


def ruled(state_file: Path | None, session: str, rnd: int) -> bool:
    if state_file is None:
        return False
    verdicts = json.loads(state_file.read_text()).get("verdicts") or []
    return any(v.get("session") == session and v.get("round") == rnd for v in verdicts)


def add(a: argparse.Namespace) -> int:
    if ruled(a.gate_state, a.session, a.round):
        return refuse(f"a verdict is already recorded for session {a.session} round {a.round}; "
                      f"not replacing {a.tree}")
    record = registered(a.repo, a.tree)
    if record is None and (a.tree.exists() or a.tree.is_symlink()):
        return refuse(f"{a.tree} exists and is not a worktree of {a.repo}")
    if record is not None:
        if "locked" in record:
            return refuse(f"{a.tree} is locked ({record['locked'] or 'no reason'}); a live run may own it")
        if a.tree.is_dir():
            check = subprocess.run([str(PREFLIGHT), "--removal", "--ignored-ok", str(a.tree)],
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
    p.add_argument("--session", required=True, help="the gate session UUID")
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--gate-state", type=Path, help="JSON printed by review_notes.py gate")
    a = parser.parse_args()
    if not a.tree.name.startswith("gate-"):
        parser.error(f"not a gate tree name: {a.tree.name}")
    return add(a)


if __name__ == "__main__":
    raise SystemExit(main())
