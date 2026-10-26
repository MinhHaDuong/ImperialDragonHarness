#!/usr/bin/env python3
"""Classify an executor stall using a bounded, worktree-keyed gate heartbeat.

One-shot by default. With --wait it polls the worktree itself, prints one line
and exits 1 on the first STALL or GATE_TIMEOUT (a wake for the launcher of a
background command), exits 0 silently at --deadline. It never kills anything.
"""

import argparse
import hashlib
import subprocess
import time
from pathlib import Path

from raid_gate_state import classify, evaluate, marker_path, read_marker

WAKE = {"STALL", "GATE_TIMEOUT"}


def snapshot(worktree: Path) -> tuple[str, str, str, str] | None:
    """Status, HEAD, pushed ref and content hash of the uncommitted diff.

    The diff hash sees a second edit of an already-modified file. A git
    failure returns None (no change); a missing upstream reads as empty.
    """
    def git(*cmd: str, optional: bool = False) -> str | None:
        try:
            done = subprocess.run(["git", "-C", str(worktree), *cmd], text=True,
                                  capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0:
            return "" if optional else None
        return done.stdout
    parts = (git("status", "--porcelain"), git("rev-parse", "HEAD"),
             git("rev-parse", "@{upstream}", optional=True), git("diff", "HEAD"))
    if any(part is None for part in parts):
        return None
    return (parts[0], parts[1], parts[2], hashlib.sha256(parts[3].encode()).hexdigest())


def run(args: argparse.Namespace, clock=time.time, sleep=time.sleep,
        take=snapshot) -> int:
    start = clock()
    state = None
    seen = None
    while True:
        now = clock()
        seen = take(args.worktree) or seen
        status, state = evaluate(now, state, seen,
                                 read_marker(marker_path(args.worktree)),
                                 args.stall_seconds, args.gate_max_seconds)
        if status in WAKE:
            print(f"{status} {args.worktree}")
            return 1
        if now - start >= args.deadline:
            return 0
        sleep(args.poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--last-progress-epoch", type=float,
                        help="latest push, worktree change, or observed gate exit")
    parser.add_argument("--gate-max-seconds", type=int, required=True,
                        help="project allowance, longer than its measured cold gate")
    parser.add_argument("--stall-seconds", type=int, default=600)
    parser.add_argument("--wait", action="store_true",
                        help="poll until STALL or GATE_TIMEOUT, then exit 1")
    parser.add_argument("--deadline", type=float, help="seconds; required with --wait")
    parser.add_argument("--poll-seconds", type=float, default=10,
                        help="at most 30, inside the heartbeat staleness")
    args = parser.parse_args()
    if args.gate_max_seconds <= args.stall_seconds:
        parser.error("gate maximum must exceed the ordinary stall window")
    if not args.worktree.is_dir():
        parser.error("worktree does not exist")
    if args.wait:
        if args.last_progress_epoch is not None:
            parser.error("--last-progress-epoch applies without --wait")
        if args.deadline is None or args.deadline <= 0:
            parser.error("--wait requires --deadline > 0")
        if not 0 < args.poll_seconds <= 30:
            parser.error("--poll-seconds must be in (0, 30]")
        return run(args)
    if args.last_progress_epoch is None:
        parser.error("--last-progress-epoch is required without --wait")
    status = classify(time.time(), args.last_progress_epoch,
                      read_marker(marker_path(args.worktree)),
                      args.stall_seconds, args.gate_max_seconds)
    print(status)
    return 0 if status in {"ACTIVE", "GATE_RUNNING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
