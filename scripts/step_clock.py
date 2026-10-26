#!/usr/bin/env python3
"""Measure a step's wall clock and print it on one stable line (ticket 1224).

    T0=$(python3 step_clock.py start)         # first thing the step does
    python3 step_clock.py end "$T0"           # last thing: prints `duration: 4m12s`

`start` prints the current epoch seconds (also `now`). `end` prints
`duration: <h>h<mm>m<ss>s | <m>m<ss>s | <s>s` from a clock read now less the
start token; a missing, malformed, or future token prints `duration: not
measured`, never a guess. Exit 0 either way: a step reports, it does not fail.

`table` reads lines `<pr> <step> <start> <end>` (epoch seconds, from `start`/`now`)
on stdin and prints one table per merge request: each step's duration, the total
from the PR's first start to its last end, and the slowest step.
"""

import sys
import time

NOT_MEASURED = 'duration: not measured'


def fmt(seconds: float) -> str:
    s = round(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f'{h}h{m:02d}m{s:02d}s'
    if m:
        return f'{m}m{s:02d}s'
    return f'{s}s'


def duration_line(token: str | None, now: float | None = None) -> str:
    try:
        elapsed = (time.time() if now is None else now) - float(token)
    except (TypeError, ValueError):
        return NOT_MEASURED
    if elapsed < 0 or elapsed != elapsed:
        return NOT_MEASURED
    return f'duration: {fmt(elapsed)}'


def table(lines: list[str]) -> str:
    rows: dict[str, list[tuple[str, float, float]]] = {}
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            rows.setdefault(parts[0], []).append((' '.join(parts[1:-2]), float(parts[-2]), float(parts[-1])))
        except ValueError:
            continue
    out = []
    for pr, steps in rows.items():
        out.append(f'PR {pr}')
        for name, a, b in steps:
            out.append(f'  {name:<16} {fmt(b - a)}')
        slowest = max(steps, key=lambda st: st[2] - st[1])
        out.append(f'  {"total":<16} {fmt(max(b for _, _, b in steps) - min(a for _, a, _ in steps))}')
        out.append(f'  slowest: {slowest[0]} ({fmt(slowest[2] - slowest[1])})')
    return '\n'.join(out) if out else 'no timed steps'


def main(argv: list[str]) -> int:
    mode = argv[0] if argv else ''
    if mode in ('start', 'now'):
        print(f'{time.time():.3f}')
    elif mode == 'end':
        print(duration_line(argv[1] if len(argv) > 1 else None))
    elif mode == 'table':
        print(table(sys.stdin.read().splitlines()))
    else:
        print('usage: step_clock.py start|now | end <start> | table < rows', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
