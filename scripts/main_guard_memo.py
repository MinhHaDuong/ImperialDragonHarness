#!/usr/bin/env python3
"""One line for the end-of-day wrap-up about the main-update guard (ticket 1180).

Reads the journal that `hooks/reference-transaction` writes for every update
of `main` (`<git-common-dir>/idh/main-journal.jsonl`) and the mode in
`git config idh.mainGuard`. While the mode is not `enforce`, it prints the
updates of `main` in the window, the `warned` and `refused` counts and the
mode, and names the ticket that holds the switch to enforce. Under `enforce`
it prints nothing unless an update was refused or warned about in the window.
A missing or unreadable journal always prints a `not checked` line: silence
must not stand for "could not look", and a missing journal can mean the hook
is not running.

Guide: docs/2026-10-21-main-update-guard.md.
"""

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("main_guard_memo")

JOURNAL = Path("idh") / "main-journal.jsonl"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
TICKET = "1180"


@dataclass
class Tally:
    updates: int = 0
    warned: int = 0
    refused: int = 0
    unreadable: int = 0


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=False)


def journal_path(repo: Path) -> Path | None:
    """The journal of the clone holding `repo`, or None outside a repository."""
    try:
        result = _git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    except OSError as exc:
        log.debug("git not runnable: %s", exc)
        return None
    if result.returncode != 0:
        log.debug("not a repository: %s", result.stderr.strip())
        return None
    return Path(result.stdout.strip()) / JOURNAL


def guard_mode(repo: Path) -> str:
    """`git config idh.mainGuard` as the hook reads it; an unset value reads as warn."""
    result = _git(repo, "config", "--get", "idh.mainGuard")
    value = result.stdout.strip() if result.returncode == 0 else ""
    if value in ("enforce", "warn", "off"):
        return value
    return "warn (unset)" if not value else f"warn ({value!r} reads as warn)"


def _parse(line: str) -> dict | None:
    try:
        entry = json.loads(line)
        entry["_when"] = datetime.strptime(entry["time"], TIME_FORMAT).replace(tzinfo=timezone.utc)
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return entry


def tally(lines: list[str], since: datetime, until: datetime) -> Tally:
    """Count the journal lines whose time falls in [since, until]."""
    counts = Tally()
    for line in lines:
        if not line.strip():
            continue
        entry = _parse(line)
        if entry is None:
            counts.unreadable += 1
            continue
        if not since <= entry["_when"] <= until:
            continue
        if entry.get("phase") == "committed":
            counts.updates += 1
        if entry.get("action") == "warned":
            counts.warned += 1
        elif entry.get("action") == "refused":
            counts.refused += 1
    return counts


def memo(repo: Path, now: datetime, hours: float) -> str | None:
    """The wrap-up line, or None when there is nothing to say under enforce."""
    path = journal_path(repo)
    if path is None:
        return f"main-guard: not checked ({repo} is not in a git repository); ticket {TICKET}."
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return (f"main-guard: not checked (no journal at {path}; the hook may not be "
                f"running); ticket {TICKET}.")
    except OSError as exc:
        return f"main-guard: not checked (journal unreadable: {exc}); ticket {TICKET}."
    mode = guard_mode(repo)
    counts = tally(lines, now - timedelta(hours=hours), now)
    if mode == "enforce" and not counts.refused and not counts.warned:
        return None
    line = (f"main-guard: {counts.updates} updates of main in the last {hours:g} h, "
            f"{counts.warned} warned, {counts.refused} refused, idh.mainGuard={mode}")
    if counts.unreadable:
        line += f", {counts.unreadable} unreadable lines skipped"
    if mode == "enforce":
        return f"{line}; ticket {TICKET}: check that each one was expected."
    return f"{line}; ticket {TICKET} holds the switch to enforce."


def _now(text: str | None) -> datetime:
    if text is None:
        return datetime.now(timezone.utc)
    return datetime.strptime(text, TIME_FORMAT).replace(tzinfo=timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=Path("."),
                        help="any checkout of the clone (default: the current directory)")
    parser.add_argument("--hours", type=float, default=24.0, help="window length (default 24)")
    parser.add_argument("--now", help="end of the window, UTC, as 2026-10-21T18:00:00Z (tests)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="%(name)s: %(message)s")
    line = memo(args.repo, _now(args.now), args.hours)
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
