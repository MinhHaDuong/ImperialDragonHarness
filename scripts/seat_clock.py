#!/usr/bin/env python3
"""Bound a review seat's wall time and name every seat's outcome (ticket 1099).

`run` launches one headless reader (any CLI: `codex exec`, `claude -p`, `pi -p`)
under a hard cap, then kills its whole process group. A seat that writes its own
report to `--out` keeps it; otherwise the reader's stdout, captured in
`<out>.stdout`, becomes the report on a clean exit. Either way one line is
printed and saved to `<out>.status`: `<seat>: reported in <s>s`, or `<seat>: no
report (timed out after <cap>s | failed to start | failed, exit <n>, <s>s |
empty output, <s>s)`. Exit 0 when reported, 1 otherwise; the caller continues.

`roster <panel>` prints one line per seat of `<panel>/manifest.txt`: its status
line when `run` wrote one after the manifest (and the report exists if the line
says reported), else `reported in <s>s` from the report's mtime less
the manifest's (the manifest is written just before launch), else `no report`.
Status lines of seats outside the manifest (optional external readers) follow.
Exit 1 when a manifest seat has no report.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_CAP_S = 600  # the panel's ten-minute collection deadline


def seat_name(out: Path) -> str:
    return out.name.removesuffix('.md')


def kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_seat(cap: int, out: Path, command: list[str]) -> tuple[bool, str]:
    # The reader's stdout goes beside the report, never onto it: a seat that
    # writes <out>.part and renames it to <out> itself keeps its report.
    captured = out.with_name(out.name + '.stdout')
    started = time.monotonic()
    try:
        with captured.open('wb') as stdout, out.with_name(out.name + '.log').open('wb') as stderr:
            try:
                child = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                         stdin=subprocess.DEVNULL, start_new_session=True)
            except OSError:
                return False, 'no report (failed to start)'
    except OSError as error:
        return False, f'no report (cannot write beside {out}: {error.strerror})'
    try:
        code = child.wait(timeout=cap)
    except subprocess.TimeoutExpired:
        kill_group(child.pid)
        child.wait()
        return False, f'no report (timed out after {cap}s)'
    kill_group(child.pid)  # reap anything the reader left running
    wall = round(time.monotonic() - started)
    if out.exists():
        return True, f'reported in {wall}s'
    if code != 0:
        return False, f'no report (failed, exit {code}, {wall}s)'
    if not captured.read_bytes().strip():
        return False, f'no report (empty output, {wall}s)'
    captured.rename(out)
    return True, f'reported in {wall}s'


def roster(panel: Path) -> tuple[bool, list[str]]:
    manifest = panel / 'manifest.txt'
    launched = manifest.stat().st_mtime
    seats = [line.split('\t')[0] for line in manifest.read_text(encoding='utf-8-sig').splitlines()
             if line.strip() and not line.startswith('#')]
    def fresh(status: Path) -> bool:  # a status older than the manifest is a past run's
        return status.exists() and status.stat().st_mtime >= launched

    complete, lines = True, []
    for seat in seats:
        status, report = panel / f'{seat}.md.status', panel / f'{seat}.md'
        line = status.read_text().strip() if fresh(status) else ''
        if line and (': reported in ' not in line or report.exists()):
            lines.append(line)
        elif report.exists():
            lines.append(f'{seat}: reported in {round(report.stat().st_mtime - launched)}s')
        else:
            lines.append(f'{seat}: no report')
        complete = complete and ': reported in ' in lines[-1]
    extras = sorted(p for p in panel.glob('*.md.status')
                    if p.name.removesuffix('.md.status') not in seats and fresh(p))
    lines += [p.read_text().strip() for p in extras]
    return complete, lines


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='mode', required=True)
    run_p = sub.add_parser('run', help='run one reader under a hard cap')
    run_p.add_argument('--cap', type=int, default=DEFAULT_CAP_S, help='wall-clock cap, seconds')
    run_p.add_argument('--out', type=Path, required=True, help='report path, <panel>/<seat>.md')
    run_p.add_argument('command', nargs='+', help='reader command, after --')
    roster_p = sub.add_parser('roster', help='one line per manifest seat')
    roster_p.add_argument('panel', type=Path)
    args = parser.parse_args(argv)
    if args.mode == 'run':
        ok, outcome = run_seat(args.cap, args.out, args.command)
        line = f'{seat_name(args.out)}: {outcome}'
        try:
            args.out.with_name(args.out.name + '.status').write_text(line + '\n')
        except OSError:
            pass  # the printed line still names the seat
        print(line)
        return 0 if ok else 1
    try:
        complete, lines = roster(args.panel)
    except OSError as error:
        print(f'seat_clock: cannot read {args.panel}/manifest.txt: {error}', file=sys.stderr)
        return 2
    print('\n'.join(lines))
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
