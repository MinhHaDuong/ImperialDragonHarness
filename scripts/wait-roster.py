#!/usr/bin/env python3
"""Block until every roster seat has filed `<dir>/<name>.md`, or a deadline passes (ticket 1327).

A gaze fork lives only while it calls tools, so its wait for seat reports is
one tool call. This is that call, shared by gaze and verify-adherence, so no
session hand-writes a sleep loop. Stdlib only; `<name>.md.part` never counts.

    wait-roster.py DIR (--roster FILE | NAME...) --until EPOCH [--slice S] [--newer-than FILE]

The roster is NAMEs, or `--roster FILE`: a gaze `manifest.txt` (parsed by
`seat_clock.manifest_items`) or any other file with one name per line. A
manifest roster also takes the manifest as `--newer-than`, as `seat_clock.py
roster` does; a report older than `--newer-than` is a past round's and does
not count; nor does a report written after `--until`. A fresh
`<name>.md.status` that does not say `reported in` (a failed headless seat
writes only that, `seat_clock.py run`) is final for the name: the wait does
not run on to the deadline for a dead seat. `--until` is an absolute epoch second (`date +%s`, plus the
deadline): the same value on every re-issue keeps the deadline across calls.

One call stays under the runtime's per-call cap (Claude Code Bash: 600 s):
`--slice` (default 540 s) bounds it. Exit codes:
  0  every roster name has its report
  1  not every name has a report: the deadline passed (missing names listed,
     one per line), or every name is final but a seat ended without a report
     (its line reads `status: <name>`); the call returns at once in that case
  2  usage error
  3  the slice ended before the deadline; re-issue the same command
"""

import argparse
import importlib.util
import sys
import time
from pathlib import Path

DEFAULT_SLICE_S = 540  # under the 600 s per-call cap of Claude Code's Bash tool
POLL_S = 2


def manifest_names(panel: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location('seat_clock', Path(__file__).with_name('seat_clock.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [cells[0] for cells in module.manifest_items(panel)]


def classify(panel: Path, names: list[str], floor: float | None, until: float) -> tuple[list[str], list[str]]:
    """The names still pending, and those final with a status line but no report."""
    def fresh(path: Path) -> bool:
        return path.is_file() and (floor is None or path.stat().st_mtime >= floor)

    pending, dead = [], []
    for name in names:
        report = panel / f'{name}.md'
        if fresh(report) and report.stat().st_mtime <= until:  # a report after the deadline is late
            continue
        status = panel / f'{name}.md.status'
        if fresh(status) and ': reported in ' not in status.read_text(errors='replace'):
            dead.append(name)
        else:
            pending.append(name)
    return pending, dead


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('dir', type=Path)
    parser.add_argument('names', nargs='*')
    parser.add_argument('--roster', type=Path)
    parser.add_argument('--until', type=float, required=True, help='absolute deadline, epoch seconds')
    parser.add_argument('--slice', type=float, default=DEFAULT_SLICE_S, dest='slice_s')
    parser.add_argument('--newer-than', type=Path, dest='newer_than')
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return 2 if exit_.code else 0
    panel, floor_file = args.dir, args.newer_than
    if not panel.is_dir() or bool(args.roster) == bool(args.names) or args.slice_s <= 0:
        print('usage: wait-roster.py DIR (--roster FILE | NAME...) --until EPOCH [--slice S]', file=sys.stderr)
        return 2
    try:
        if args.roster is None:
            names = args.names
        elif args.roster.name == 'manifest.txt':
            names = manifest_names(args.roster.parent)
            floor_file = floor_file or args.roster
        else:
            names = [line.strip() for line in args.roster.read_text(encoding='utf-8-sig').splitlines()
                     if line.strip() and not line.startswith('#')]
        floor = floor_file.stat().st_mtime if floor_file else None
    except OSError as error:
        print(f'wait-roster: {error}', file=sys.stderr)
        return 2
    if not names:
        print('wait-roster: empty roster', file=sys.stderr)
        return 2
    slice_end = time.time() + args.slice_s
    while True:
        gone, dead = classify(panel, names, floor, args.until)
        now = time.time()
        lines = gone + [f'status: {name}' for name in dead]
        if not gone:
            if dead:
                print('\n'.join(lines))
            return 1 if dead else 0
        if now > args.until:
            print('\n'.join(lines))
            print(f'wait-roster: deadline passed, {len(gone) + len(dead)} of {len(names)} without a report',
                  file=sys.stderr)
            return 1
        if now >= slice_end:
            print(f'wait-roster: slice of {args.slice_s:g}s ended, {len(gone)} of {len(names)} missing, '
                  f'{args.until - now:.0f}s to the deadline; re-issue the same command', file=sys.stderr)
            return 3
        time.sleep(min(POLL_S, args.until - now, slice_end - now))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
