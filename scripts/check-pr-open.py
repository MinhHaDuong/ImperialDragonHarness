#!/usr/bin/env python3
"""Stop a review phase when its pull request is no longer open."""

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", type=int)
    parser.add_argument("phase")
    parser.add_argument("--timeout-seconds", type=float, default=10)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(args.pr), "--json", "state", "--jq", ".state"],
            capture_output=True,
            text=True,
            check=False,
            timeout=args.timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        print(f"/gaze stopped: phase={args.phase} state=UNKNOWN pr={args.pr}", file=sys.stderr)
        print(f"PR state check timed out after {args.timeout_seconds:g}s", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"/gaze stopped: phase={args.phase} state=UNKNOWN pr={args.pr}", file=sys.stderr)
        print(f"PR state check failed: {exc}", file=sys.stderr)
        return 3
    state = result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    if state == "OPEN":
        return 0
    if state not in {"MERGED", "CLOSED"}:
        state = "UNKNOWN"
    print(f"/gaze stopped: phase={args.phase} state={state} pr={args.pr}", file=sys.stderr)
    if result.returncode != 0 and result.stderr.strip():
        print(f"PR state check failed: {result.stderr.strip()}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
