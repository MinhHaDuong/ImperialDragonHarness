#!/usr/bin/env python3
"""Tally bump and note log entries per ticket for RAID wrap-up step 1b.

Port of the awk recipe in skills/raid/SKILL.md (ticket 1086). Prints
`Ticket NNNN: N kind` lines, bytewise sorted, for each ticket log section.

Drift: a log section with entries but no line in the timestamp shape
`YYYY-` is reported on stderr and that file contributes nothing. Exit stays
0 so a `set -e` wrap-up continues. Exit 2 means no ticket directory was
found, so the repo cannot be read at all.

Known limit: the drift check catches timestamp-shape changes only. A verb
rename (bump -> reroll) still yields zeros with no warning.
"""

import argparse
import logging
import re
import sys
from collections import Counter
from pathlib import Path

LOG_OPEN = "--- log ---"
BODY_OPEN = "--- body ---"
ENTRY_SHAPE = re.compile(r"[0-9]{4}-")
VERB = re.compile(r" (bump|note) ")
FIELD = re.compile(r"[^ \t\n]+")
KEPT_NOTES = {"verify-reroll", "circuit-breaker"}

log = logging.getLogger("raid-reroll-tally")


def tally_file(path: Path, counts: Counter[tuple[str, str]]) -> bool:
    """Count the log entries of one ticket file; return True on drift."""
    ticket = path.name[:4]
    text = path.read_bytes().decode("utf-8", errors="replace")
    in_log = False
    has_text = False
    has_shape = False
    for line in text.split("\n"):
        if line == BODY_OPEN:
            break
        if line == LOG_OPEN:
            in_log = True
            continue
        if not in_log:
            continue
        if line.strip(" \t"):
            has_text = True
        if not ENTRY_SHAPE.match(line):
            continue
        has_shape = True
        match = VERB.search(line)
        if not match:
            continue
        fields = FIELD.findall(line[match.start() + 1:])
        verb = fields[0]
        kind = fields[1] if len(fields) > 1 else ""
        if verb == "note" and kind == "bump" and fields[2:3] == ["verify-reroll"]:
            kind = "verify-reroll"
        if verb == "note" and kind not in KEPT_NOTES:
            continue
        counts[(ticket, kind)] += 1
    drift = has_text and not has_shape
    if drift:
        log.warning("drift: %s has log entries, none in the timestamp shape; "
                    "its counts are not trusted", path.name)
    return drift


def ticket_files(dirs: list[Path]) -> list[Path]:
    found = [d for d in dirs if d.is_dir()]
    if not found:
        return []
    return [p for d in found for p in sorted(d.glob("*.erg"))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dirs", nargs="+", type=Path, help="ticket directories to scan")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    if not any(d.is_dir() for d in args.dirs):
        log.error("no ticket directory found among: %s", " ".join(map(str, args.dirs)))
        return 2
    counts: Counter[tuple[str, str]] = Counter()
    for path in ticket_files(args.dirs):
        tally_file(path, counts)
    lines = [f"Ticket {ticket}: {n} {kind}" for (ticket, kind), n in counts.items()]
    for line in sorted(lines):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
