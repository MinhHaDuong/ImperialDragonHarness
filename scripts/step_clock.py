#!/usr/bin/env python3
"""Measure a step's wall clock and print it on one stable line (ticket 1224).

    python3 step_clock.py start               # first thing the step does: prints a token
    python3 step_clock.py end <token>         # last thing: prints `duration: 4m12s`

Shell variables do not persist between a runtime's Bash calls: carry the printed
token literally into the later call. `end --seconds <token>` prints whole seconds
(`na` when not measured) for a numeric field.

`start` prints the current epoch seconds (also `now`). `end` prints
`duration: <h>h<mm>m<ss>s | <m>m<ss>s | <s>s` from a clock read now less the
start token; a missing, malformed, or future token prints `duration: not
measured`, never a guess. Exit 0 either way: a step reports, it does not fail.

`table` reads lines `<pr> <step> <start> <end>` (epoch seconds, from `start`/`now`)
on stdin and prints one table per merge request: each step's duration, the total
from the PR's first start to its last end, and the slowest step.
"""

import math
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


def elapsed_since(token: str | None, now: float | None = None) -> float | None:
    try:
        start = float(token)
        elapsed = (time.time() if now is None else now) - start
    except (TypeError, ValueError):
        return None
    return elapsed if start > 0 and elapsed >= 0 else None  # also rejects NaN


def duration_line(token: str | None, now: float | None = None) -> str:
    elapsed = elapsed_since(token, now)
    return NOT_MEASURED if elapsed is None else f'duration: {fmt(elapsed)}'


def table(lines: list[str]) -> str:
    rows: dict[str, list[tuple[str, float, float]]] = {}
    bad: dict[str, list[str]] = {}  # unreadable rows are listed, never dropped
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        if len(parts) < 4:
            bad.setdefault(parts[0], []).append(' '.join(parts[1:]) or '?')
            continue
        try:
            a, b = float(parts[-2]), float(parts[-1])
            if not (math.isfinite(a) and math.isfinite(b)) or a <= 0 or b < a:
                raise ValueError
            rows.setdefault(parts[0], []).append((' '.join(parts[1:-2]), a, b))
        except ValueError:
            bad.setdefault(parts[0], []).append(' '.join(parts[1:-2]))
    out = []
    for pr in dict.fromkeys([*rows, *bad]):
        steps = rows.get(pr, [])
        out.append(f'PR {pr}')
        for name in bad.get(pr, []):
            out.append(f'  {name:<16} not measured')
        if not steps:
            continue
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
        token = argv[-1] if len(argv) > 1 else None
        if '--seconds' in argv:  # whole seconds for a numeric field; `na` when not measured
            elapsed = elapsed_since(token)
            print('na' if elapsed is None else round(elapsed))
        else:
            print(duration_line(token))
    elif mode == 'table':
        print(table(sys.stdin.read().splitlines()))
    else:
        print('usage: step_clock.py start|now | end <start> | table < rows', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
