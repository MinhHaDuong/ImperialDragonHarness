#!/usr/bin/env python3
"""The raid log: one append-only text file shared by every worktree of a repo.

Path: `$IDH_RAID_LOG`, else `<git common dir>/idh-raid/raid.log` (untracked,
survives worktree removal). One line per event: `<epoch> <EVENT> k=v ...`.
Every line carries `raid=<id>`, the id of the raid that wrote it, so concurrent
raids share the file without mixing. `append RAID_START` mints a short random id
unless `raid=` is given and prints the line; read the id there and pass it on
every later append.

    raid_log.py append RAID_START deadline=1700007200   # prints raid=<new id>
    raid_log.py append WAVE_BASE raid=ab12cd sha=abc123  # time stamped now
    raid_log.py path
"""

import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

LINE = re.compile(r"^(\d+(?:\.\d+)?) ([A-Z][A-Z_]*)((?: [A-Za-z_]+=\S*)*)$")


def log_path(cwd: Path | None = None) -> Path:
    override = os.environ.get("IDH_RAID_LOG")
    if override:
        return Path(override)
    done = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, cwd=cwd, timeout=10)
    if done.returncode != 0:
        raise RuntimeError("not in a git repository: " + done.stderr.strip())
    return Path(done.stdout.strip()) / "idh-raid" / "raid.log"


def append(event: str, fields: dict[str, str], path: Path, now: float | None = None) -> str:
    fields = dict(fields)
    if event == "RAID_START":
        fields.setdefault("raid", secrets.token_hex(3))
    elif not fields.get("raid"):
        raise ValueError(f"{event} needs raid=<id>, printed by the RAID_START line")
    line = f"{int(now if now is not None else time.time())} {event}"
    line += "".join(f" {k}={v}" for k, v in fields.items())
    if not LINE.match(line):
        raise ValueError(f"not a valid raid log line: {line!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(line + "\n")
    return line


def parse(text: str) -> tuple[list[tuple[float, str, dict[str, str]]], list[int]]:
    """Events in file order, and the 1-based numbers of lines that did not parse."""
    events, bad = [], []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        match = LINE.match(raw)
        if not match:
            bad.append(number)
            continue
        fields = dict(pair.split("=", 1) for pair in match.group(3).split())
        events.append((float(match.group(1)), match.group(2), fields))
    return events, bad


def main(argv: list[str]) -> int:
    if len(argv) >= 1 and argv[0] == "path":
        print(log_path())
        return 0
    if len(argv) >= 2 and argv[0] == "append":
        try:
            fields = dict(item.split("=", 1) for item in argv[2:])
            print(append(argv[1], fields, log_path()))
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
            print(f"raid_log: {error}", file=sys.stderr)
            return 2
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
