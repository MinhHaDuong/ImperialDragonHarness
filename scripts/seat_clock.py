#!/usr/bin/env python3
"""Bound a review seat's wall time and name every seat's outcome (ticket 1099).

`run` launches one headless reader (any CLI: `codex exec`, `claude -p`, `pi -p`)
under a hard cap, then kills its whole process group. A seat that writes its own
report to `--out` during this run keeps it (a past run's file does not count); otherwise the reader's stdout, captured in
`<out>.stdout`, becomes the report on a clean exit. Either way one line is
printed and saved to `<out>.status`: `<seat>: reported in <s>s`, or `<seat>: no
report (timed out after <cap>s | failed to start | failed, exit <n>, <s>s |
empty output, <s>s)`. Exit 0 when reported, 1 otherwise; the caller continues.

`roster <panel>` prints one line per seat of `<panel>/manifest.txt`. Only files
newer than the manifest count (the panel directory is reused across rounds): the
seat's status line from `run` (if it says reported, the report must be fresh too),
else `reported in <s>s` from the report's mtime less the manifest's (the
manifest is written just before launch), else `no report`. Fresh status lines of
seats outside the manifest (optional external readers) follow. Exit 1 when a
manifest seat has no report or the manifest lists no seat.

`plan-check <panel>` compares gaze's plan (the manifest: one item per line,
`# budget: <n>m` in its header) with what ran (ticket 1225). Its first line is
`plan check: PASS`, `plan check: PASS with deviations — ...` or `plan check:
FAIL — ...`; the roster lines follow. An item with no report fails it. A worker
whose report is empty, does not open with `worker: model=<id> ·
family=<family>` (leading blank lines and Markdown bold tolerated), or holds
that line alone did not report either, which fails it too; one that names no
family or another family than planned, or an item over the budget, is a
deviation. An item planned with family `none` (a script) needs only a
non-empty report. Exit 1 on FAIL only.

`plan-write <panel> --intent T --method T --budget <n>m [--spend T] --item NAME
MODEL FAMILY REASON ...` writes `<panel>/manifest.txt` (ticket 1267): the header
and TAB lines are built here and checked by `panel-manifest-check.py` before
anything is written, so a manifest the plan check cannot parse is never
produced. Exit 2 and no file on a refused plan.
"""

import argparse
import importlib.util
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

MAX_BUDGET_M = 13  # 15-minute deadline less the closing (skills/gaze/references/plan.md)
DEFAULT_CAP_S = 600  # the panel's ten-minute collection deadline


def seat_name(out: Path) -> str:
    return out.name.removesuffix('.md')


def kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_seat(cap: int, out: Path, command: list[str], cwd: Path | None = None,
             stdin: Path | None = None, env: dict[str, str] | None = None) -> tuple[bool, str]:
    # The reader's stdout goes beside the report, never onto it: a seat that
    # writes <out>.part and renames it to <out> itself keeps its report.
    # `cwd` pins the reader to the review tree; `stdin` feeds it a prompt file
    # (gaze_seat.py, ticket 1256), else it reads nothing; `env` adds variables to
    # the reader's environment (ticket 1279: Vibe's disposable VIBE_HOME).
    captured = out.with_name(out.name + '.stdout')
    started, launched = time.monotonic(), time.time() - 1  # 1 s for filesystem stamp granularity
    try:
        with captured.open('wb') as stdout, out.with_name(out.name + '.log').open('wb') as stderr:
            try:
                with (stdin.open('rb') if stdin else open(os.devnull, 'rb')) as feed:
                    child = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=feed,
                                             cwd=cwd, start_new_session=True,
                                             env={**os.environ, **env} if env else None)
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
    if out.exists() and out.stat().st_mtime >= launched:  # a past run's report does not count
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
    if not seats:
        return False, ['no seats in manifest']

    def fresh(path: Path) -> bool:  # a file older than the manifest is a past round's
        return path.exists() and path.stat().st_mtime >= launched

    def seat_line(seat: str) -> str:
        status, report = panel / f'{seat}.md.status', panel / f'{seat}.md'
        line = status.read_text().strip() if fresh(status) else ''
        if line and (': reported in ' not in line or fresh(report)):
            return line
        if fresh(report):
            return f'{seat}: reported in {round(report.stat().st_mtime - launched)}s'
        return f'{seat}: no report'

    lines = [seat_line(seat) for seat in seats]
    complete = all(': reported in ' in line for line in lines)
    extras = sorted(name for p in panel.glob('*.md.status')
                    if (name := p.name.removesuffix('.md.status')) not in seats and fresh(p))
    lines += [seat_line(name) for name in extras]
    return complete, lines


def plan_check(panel: Path) -> tuple[bool, list[str]]:
    complete, lines = roster(panel)
    manifest = (panel / 'manifest.txt').read_text(encoding='utf-8-sig').splitlines()
    budget = next((int(m.group(1)) * 60 for line in manifest
                   if (m := re.fullmatch(r'# budget: (\d+)m', line.strip()))), None)
    missing, deviations = [], []
    by_name = {line.split(': ', 1)[0]: line for line in lines}
    for cells in (line.split('\t') for line in manifest if line.strip() and not line.startswith('#')):
        name, planned = cells[0], cells[2].strip() if len(cells) > 2 else ''
        line = by_name.get(name, f'{name}: no report')
        timed = re.search(r': reported in (\d+)s', line)
        if not timed:
            missing.append(line)
            continue
        if budget is not None and int(timed.group(1)) > budget:
            deviations.append(f'{name}: {timed.group(1)}s, over the {budget // 60}m budget')
        text = (panel / f'{name}.md').read_text(encoding='utf-8-sig', errors='replace')
        lines_ = [ln.strip().strip('*').strip() for ln in text.splitlines() if re.search(r'\w', ln)]
        first = lines_[0] if lines_ else ''
        signed = first.lower().startswith('worker:')
        if not lines_ or (planned != 'none' and (not signed or len(lines_) < 2)):
            missing.append(f'{name}: no report (empty, unsigned, or the worker line alone)')
            continue
        if planned == 'none':
            continue
        named = re.search(r'family=([\w.-]+)', first, re.IGNORECASE)
        if not named:
            deviations.append(f'{name}: names no family, planned {planned}')
        elif named.group(1).lower() != planned.lower():
            deviations.append(f'{name}: family {named.group(1)}, planned {planned}')
    if missing or not complete:
        head = 'plan check: FAIL — ' + '; '.join(missing + deviations)
    elif deviations:
        head = 'plan check: PASS with deviations — ' + '; '.join(deviations)
    else:
        head = 'plan check: PASS'
    return not missing and complete, [head, *lines]


def plan_write(panel: Path, intent: str, method: str, budget: str, spend: str | None,
               items: list[list[str]]) -> list[str]:
    """Write the manifest; return the problems (nothing is written when any)."""
    spec = importlib.util.spec_from_file_location(
        'panel_manifest_check', Path(__file__).with_name('panel-manifest-check.py'))
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    flat = [cell for item in items for cell in item] + [intent, method, budget, spend or '']
    early = []
    if any(re.search('[\udc80-\udcff]', cell) for cell in flat + [str(panel)]):
        return ['an argument is not valid UTF-8']
    if not intent.strip():
        early.append('empty --intent')
    if not (m := re.fullmatch(r'(\d+)m', budget)) or not 1 <= int(m.group(1)) <= MAX_BUDGET_M:
        early.append(f'--budget must be <n>m with n from 1 to {MAX_BUDGET_M}')
    early += [f'family {item[2]!r} holds whitespace' for item in items if re.search(r'\s', item[2])]
    if early:
        return early
    if any(c in cell for cell in flat for c in '\t\n\r'):
        return ['a tab or newline inside a field']
    header = [f'# intent: {intent}', f'# method: {method}', f'# budget: {budget}']
    if spend:
        header.append(f'# spend: {spend}')
    text = '\n'.join(header + ['\t'.join(item) for item in items]) + '\n'
    problems = checker.check(text)
    if not problems:
        panel.mkdir(parents=True, exist_ok=True)
        (panel / 'manifest.txt').write_text(text, encoding='utf-8')
    return problems


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='mode', required=True)
    run_p = sub.add_parser('run', help='run one reader under a hard cap')
    run_p.add_argument('--cap', type=int, default=DEFAULT_CAP_S, help='wall-clock cap, seconds')
    run_p.add_argument('--out', type=Path, required=True, help='report path, <panel>/<seat>.md')
    run_p.add_argument('command', nargs='+', help='reader command, after --')
    roster_p = sub.add_parser('roster', help='one line per manifest seat')
    roster_p.add_argument('panel', type=Path)
    plan_p = sub.add_parser('plan-check', help='the plan against what ran')
    plan_p.add_argument('panel', type=Path)
    write_p = sub.add_parser('plan-write', help='write a validated manifest')
    write_p.add_argument('panel', type=Path)
    write_p.add_argument('--intent', required=True)
    write_p.add_argument('--method', required=True)
    write_p.add_argument('--budget', required=True, help='<n>m')
    write_p.add_argument('--spend')
    write_p.add_argument('--item', nargs=4, action='append', default=[],
                         metavar=('NAME', 'MODEL', 'FAMILY', 'REASON'))
    args = parser.parse_args(argv)
    if args.mode == 'plan-write':
        problems = plan_write(args.panel, args.intent, args.method, args.budget, args.spend, args.item)
        for problem in problems:
            print(f'seat_clock: plan refused: {problem}', file=sys.stderr)
        if not problems:
            print(f'plan written: {args.panel}/manifest.txt')
        return 2 if problems else 0
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
        complete, lines = (plan_check if args.mode == 'plan-check' else roster)(args.panel)
    except OSError as error:
        print(f'seat_clock: cannot read {args.panel}/manifest.txt: {error}', file=sys.stderr)
        return 2
    print('\n'.join(lines))
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
