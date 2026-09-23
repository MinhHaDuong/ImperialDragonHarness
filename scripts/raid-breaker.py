#!/usr/bin/env python3
"""Classify an executor stall using a bounded, worktree-keyed gate heartbeat."""

import argparse
import time
from pathlib import Path

from raid_gate_state import classify, marker_path, read_marker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--last-progress-epoch", type=float, required=True,
                        help="latest push, worktree change, or observed gate exit")
    parser.add_argument("--gate-max-seconds", type=int, required=True,
                        help="project allowance, longer than its measured cold gate")
    parser.add_argument("--stall-seconds", type=int, default=600)
    args = parser.parse_args()
    if args.gate_max_seconds <= args.stall_seconds:
        parser.error("gate maximum must exceed the ordinary stall window")
    if not args.worktree.is_dir():
        parser.error("worktree does not exist")
    now = time.time()
    status = classify(now, args.last_progress_epoch,
                      read_marker(marker_path(args.worktree)),
                      args.stall_seconds, args.gate_max_seconds)
    print(status)
    return 0 if status in {"ACTIVE", "GATE_RUNNING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
