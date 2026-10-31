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


SITREP_DOC = Path(__file__).resolve().parent.parent / "skills/raid/references/sitrep.md"
NUMERIC = {"n"}  # keys the doc row describes as counts


def event_table(doc: Path = SITREP_DOC) -> dict[str, tuple[list[str], list[str] | None]]:
    """Event -> (required keys, allowed `step=` values or None), read from the sitrep doc's event table,
    the single source of the key rows. A field cell lists `key=` in backticks; one preceded by `optional`
    is not required; the backticked words in the parentheses after `step=` are the allowed steps."""
    table = {}
    for row in doc.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        match = re.fullmatch(r"`([A-Z][A-Z_]*)`", cells[0]) if len(cells) == 3 else None
        if not match:
            continue
        cell = cells[2]
        required = [k for opt, k in re.findall(r"(optional )?`(\w+)=", cell) if not opt]
        step = re.search(r"`step=`\s*\(([^)]*)\)", cell)
        table[match[1]] = (required, re.findall(r"`(\w+)`", step[1]) if step else None)
    return table


def check_fields(event: str, fields: dict[str, str], doc: Path = SITREP_DOC) -> None:
    """ValueError naming the missing key and the expected form when the event lacks a documented key."""
    required, steps = event_table(doc).get(event, ([], None))
    for key in required:
        if key == "raid" and event == "RAID_START":
            continue  # minted when absent
        if not fields.get(key):
            expected = f"{event} " + " ".join(f"{k}=<{'number' if k in NUMERIC else k}>" for k in required)
            raise ValueError(f"{event} is missing {key}=; expected form: {expected}")
    for key in NUMERIC & fields.keys() & set(required):
        if not re.fullmatch(r"\d+", fields[key]):
            raise ValueError(f"{event} {key}= must be a number, got {fields[key]!r}")
    if steps and "step" in fields and not any(re.fullmatch(s.replace("N", r"\d+"), fields["step"]) for s in steps):
        raise ValueError(f"{event} step= must be one of {', '.join(steps)}; got {fields['step']!r}")


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
        if not fields.get("raid"):
            fields["raid"] = secrets.token_hex(3)
    elif not fields.get("raid"):
        raise ValueError(f"{event} needs raid=<id>, printed by the RAID_START line")
    check_fields(event, fields)
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
