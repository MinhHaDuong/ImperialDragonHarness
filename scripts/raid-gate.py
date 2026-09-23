#!/usr/bin/env python3
"""Run a project gate with a heartbeat the raid breaker can observe."""

import argparse
import subprocess
import time
from pathlib import Path

from raid_gate_state import marker_path, write_marker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a gate command is required after --")
    marker = marker_path(Path.cwd())
    started = time.time()
    write_marker(marker, started, started)
    try:
        process = subprocess.Popen(command)
        while True:
            try:
                return process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    write_marker(marker, started, time.time())
                except OSError:
                    process.terminate()
                    process.wait(timeout=5)
                    raise
    finally:
        marker.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
