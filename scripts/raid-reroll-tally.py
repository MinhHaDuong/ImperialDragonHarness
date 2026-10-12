#!/usr/bin/env python3
"""Tally bump and note log entries per ticket for RAID wrap-up step 1b.

Ported from the awk recipe that lived inline in skills/raid/SKILL.md; the
awk is kept as the differential oracle in tests/test_raid_reroll_tally.py
(ticket 1086). Prints `Ticket NNNN: N kind` lines, bytewise sorted.

Drift (warning on stderr, exit 0, so a `set -e` wrap-up continues; the
entries that did parse are still counted):
  - a log line not in the timestamp shape `YYYY-`;
  - a ticket file with no `--- log ---` marker;
  - an empty tally although log entries exist (verb rename, e.g. bump -> reroll).

Could not look (exit 2, rows already counted are still printed): no ticket
directory exists, a directory cannot be listed, or a ticket file cannot be read.
An all-clear is never printed for a corpus the script could not read.
"""

import argparse
import logging
import os
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


def tally_file(path: Path, counts: Counter[tuple[str, str]]) -> int:
    """Count the log entries of one ticket file; return how many it holds."""
    ticket = path.name[:4]
    text = path.read_bytes().decode("utf-8", errors="replace")
    in_log = False
    has_log = False
    unshaped = 0
    entries = 0
    for raw in text.split("\n"):
        line = raw.removesuffix("\r")
        if line == BODY_OPEN:
            break
        if line == LOG_OPEN:
            in_log = True
            has_log = True
            continue
        if not in_log:
            continue
        if not ENTRY_SHAPE.match(line):
            if line.strip(" \t"):
                unshaped += 1
            continue
        entries += 1
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
    if unshaped:
        log.warning("drift: %s has %d log line(s) not in the timestamp shape; "
                    "those entries are not counted", path.name, unshaped)
    if not has_log:
        log.warning("drift: %s has no '%s' marker; its entries are not counted",
                    path.name, LOG_OPEN)
    return entries


def ticket_files(dirs: list[Path]) -> tuple[list[Path], bool]:
    """Ticket files directly under each existing dir; dotfiles and dirs skipped.

    The flag is True when a directory exists but cannot be listed.
    """
    found: list[Path] = []
    unreadable = False
    for d in dirs:
        if not d.is_dir():
            continue
        try:
            names = sorted(os.listdir(d))
        except OSError as err:
            log.error("cannot read directory %s: %s", d, err.strerror)
            unreadable = True
            continue
        found += [d / n for n in names
                  if n.endswith(".erg") and not n.startswith(".") and (d / n).is_file()]
    return found, unreadable


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
    paths, failed = ticket_files(args.dirs)
    entries = 0
    for path in paths:
        try:
            entries += tally_file(path, counts)
        except OSError as err:
            log.error("cannot read %s: %s", path, err.strerror)
            failed = True
    if entries and not counts:
        log.warning("drift: %d log entries in %d files, none a bump or note; "
                    "the log format or verbs may have changed", entries, len(paths))
    lines = [f"Ticket {ticket}: {n} {kind}" for (ticket, kind), n in counts.items()]
    for line in sorted(lines):
        print(line)
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
