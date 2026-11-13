#!/usr/bin/env python3
"""List overdue foreign requests that have no named owner branch or lock.

Uses the workflow cross-project provenance convention. With --ref, tickets
come from that committed snapshot; owner signals always use current local
and remote refs and locked worktrees. No forge or process-liveness inference.
"""

import argparse
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import re
import subprocess
import sys


PROVENANCE = re.compile(
    r"^(\S+) \S+ note filed from (\S+) (\S+)\s*$", re.MULTILINE
)
TICKET_NAME = re.compile(r"(?<![a-zA-Z0-9])t?0*(\d+)(?![a-zA-Z0-9])")


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, text=True,
        capture_output=True,
    ).stdout


def owner_tickets(repo):
    names = git(repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")
    owned = {int(match.group(1)) for match in TICKET_NAME.finditer(names)}
    for entry in git(repo, "worktree", "list", "--porcelain").split("\n\n"):
        if any(line.startswith("locked") for line in entry.splitlines()):
            # Only explicit ticket markers count in locks: PIDs and path suffixes
            # often contain unrelated numbers.
            owned.update(int(match) for match in re.findall(
                r"(?<![a-zA-Z0-9])t0*(\d+)(?![a-zA-Z0-9])", entry
            ))
    return owned


def ticket_texts(repo, ref):
    if ref:
        paths = git(repo, "ls-tree", "-r", "--name-only", ref, "--", "tickets/").splitlines()
        for path in paths:
            if re.fullmatch(r"tickets/\d{4}-[^/]+\.erg", path):
                yield path, git(repo, "show", f"{ref}:{path}")
    else:
        for path in sorted((repo / "tickets").glob("[0-9][0-9][0-9][0-9]-*.erg")):
            yield path.name, path.read_text()


def overdue(repo, ref, now):
    owned = owner_tickets(repo)
    for path, text in ticket_texts(repo, ref):
        number = int(Path(path).name.split("-", 1)[0])
        header, separator, rest = text.partition("--- log ---")
        if not separator or re.search(r"^Closed:\s*\S", header, re.MULTILINE) or number in owned:
            continue
        log = rest.partition("--- body ---")[0]
        for stamp, asker, ticket in PROVENANCE.findall(log):
            filed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if now - filed <= timedelta(days=1):
                continue
            title = re.search(r"^Title: *(.*)$", header, re.MULTILINE)
            yield f"{number:04d} | {title.group(1) if title else Path(path).stem} | filed from {asker} {ticket} | {stamp}"
            break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--ref", help="Read tickets from this git snapshot instead of the working tree")
    parser.add_argument("--now", help="Override UTC current time with an ISO timestamp")
    args = parser.parse_args()
    try:
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
        if now.tzinfo is None:
            parser.error("--now must include a UTC offset")
        for row in overdue(args.repo, args.ref, now):
            sys.stdout.write(row + "\n")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        logging.error("Foreign tickets NOT inspected: %s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
