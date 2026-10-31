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
non-empty report. A `# no-door:` header is a deviation
too, so the posted line shows it. Exit 1 on FAIL only.

`seats <panel>` prints `seats: panel` when an item other than self (name or
model `self`) filed a report the plan check accepts, else `seats: self-only`.

`identities <panel> [--session-runtime R] [--session-model M]` prints one `seat:` line
per worker item of the manifest (ticket 1303), built from the plan and the
launcher-set `worker:` header, never typed by the model: `seat: <item> ·
runtime=<id> · family=<family> · route=<token> · model=<provider/id | not
observed> · status: ran|failed|skipped`. A header with `door=headless` is the
launcher's (its runtime and model) only when `launches.jsonl` holds a launch line for that seat and this
unit (`IDH_UNIT`, else the branch; ticket 1399); the plan's reason text never decides, and an unreadable
archive trusts no header, with one warning. Any other seat typed its own header, so its line takes the manifest pin and the session's runtime (`route=subagent`), and its
family is the runtime door's (routes.json), the model's `<provider>/` prefix, else `unconfirmed`,
never the plan label (a mismatch prints a `deviation:` line on stderr, ticket 1360);
self takes the session's runtime and model (`route=self`); a seat with no
report keeps its planned pin and the runtime its reason names, status `failed`.
Items of family `none` (scripts) are not workers and print nothing. The model id
is provider-qualified by the door's billed provider (`gaze_seat.billed_provider`).
Session values default from `IDH_SESSION_RUNTIME` and `IDH_SESSION_MODEL`.

`plan-write <panel> --intent T --method T --budget <n>m [--spend T]
[--no-door T] --item NAME MODEL FAMILY
REASON ...` writes `<panel>/manifest.txt` (ticket 1267): the header and TAB
lines are built here and checked by `panel-manifest-check.py` before anything
is written, so a manifest the plan check cannot parse is never produced. It
also refuses (ticket 1287) a plan whose every item is self, unless `--no-door`
names the doors tried; that flag becomes a header line. Exit 2 and no file on a refused plan.
"""

import argparse
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import launch_line  # noqa: E402  (ticket 1384)

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
             stdin: Path | None = None, env: dict[str, str] | None = None,
             replace_env: bool = False, launch: dict | None = None) -> tuple[bool, str]:
    """Run one seat; with `launch` ({'seat', optional 'spool'}) append its launch line on every return
    path (ticket 1384). The line is bookkeeping: a failed write warns and never changes the outcome."""
    info: dict = {}
    started = time.time()
    try:
        return _run_seat(cap, out, command, cwd, stdin, env, replace_env, info)
    finally:
        if launch is not None:
            try:
                runtime, session = launch_line.child_from(command, out.with_name(out.name + '.log'),
                                                          launch.get('spool'))
                launch_line.record(seat=launch['seat'], child_runtime=runtime, child_session=session,
                                   ts_start=started, ts_end=time.time(), exit=info.get('exit', 'failed to start'),
                                   cwd=cwd)
            except Exception as error:  # bookkeeping never changes the seat's outcome
                print(f'launch_line: {error}', file=sys.stderr)


def _run_seat(cap, out, command, cwd, stdin, env, replace_env, info) -> tuple[bool, str]:
    # The reader's stdout goes beside the report, never onto it: a seat that
    # writes <out>.part and renames it to <out> itself keeps its report.
    # `cwd` pins the reader to the review tree; `stdin` feeds it a prompt file
    # (gaze_seat.py, ticket 1256), else it reads nothing; `env` adds variables to
    # the reader's environment (ticket 1279: Vibe's disposable VIBE_HOME); with
    # `replace_env` it is the reader's whole environment and nothing is inherited
    # (ticket 1376: gaze_seat.py's allowlist).
    captured = out.with_name(out.name + '.stdout')
    started, launched = time.monotonic(), time.time() - 1  # 1 s for filesystem stamp granularity
    try:
        with captured.open('wb') as stdout, out.with_name(out.name + '.log').open('wb') as stderr:
            try:
                with (stdin.open('rb') if stdin else open(os.devnull, 'rb')) as feed:
                    child = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=feed,
                                             cwd=cwd, start_new_session=True,
                                             env=env if replace_env else {**os.environ, **env} if env else None)
            except OSError:
                return False, 'no report (failed to start)'
    except OSError as error:
        return False, f'no report (cannot write beside {out}: {error.strerror})'
    try:
        code = child.wait(timeout=cap)
    except subprocess.TimeoutExpired:
        kill_group(child.pid)
        child.wait()
        info['exit'] = 'timeout'
        return False, f'no report (timed out after {cap}s)'
    info['exit'] = code
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


def manifest_items(panel: Path) -> list[list[str]]:
    """The plan items of `<panel>/manifest.txt`, each as its tab-separated cells."""
    return [line.split('\t') for line in (panel / 'manifest.txt').read_text(encoding='utf-8-sig').splitlines()
            if line.strip() and not line.startswith('#')]


def roster(panel: Path) -> tuple[bool, list[str]]:
    manifest = panel / 'manifest.txt'
    launched = manifest.stat().st_mtime
    seats = [cells[0] for cells in manifest_items(panel)]
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


def is_self(item: list[str]) -> bool:
    """Gaze's own read: item name `self`, or model `self` (references/plan.md, the plan file)."""
    return item[0] == 'self' or (len(item) > 1 and item[1].strip() == 'self')


def plan_check(panel: Path) -> tuple[bool, list[str]]:
    ok, lines, _ = assess(panel)
    return ok, lines


def assess(panel: Path) -> tuple[bool, list[str], list[str]]:
    """The plan check, plus the non-self items whose report it accepted."""
    ok, lines, reported, _ = _assess(panel)
    return ok, lines, reported


def seats(panel: Path) -> str:
    """`seats: panel` when an item other than self filed a report the plan check accepts."""
    _, _, reported = assess(panel)
    return 'seats: panel' if reported else 'seats: self-only'


def _assess(panel: Path) -> tuple[bool, list[str], list[str], list[str]]:
    """The plan check, the non-self items whose report it accepted, and every item it accepted."""
    complete, lines = roster(panel)
    manifest = (panel / 'manifest.txt').read_text(encoding='utf-8-sig').splitlines()
    budget = next((int(m.group(1)) * 60 for line in manifest
                   if (m := re.fullmatch(r'# budget: (\d+)m', line.strip()))), None)
    missing, deviations, reported, accepted = [], [], [], []
    deviations += [f'no door launched: {line.split(":", 1)[1].strip()}' for line in manifest
                   if line.startswith('# no-door:')]
    by_name = {line.split(': ', 1)[0]: line for line in lines}
    for cells in manifest_items(panel):
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
        accepted.append(name)
        if not is_self(cells):
            reported.append(name)
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
    return not missing and complete, [head, *lines], reported, accepted


def worker_header(report: Path) -> dict[str, str]:
    """The `key=value` fields of a report's first line when it is a `worker:` line, else {}."""
    try:
        text = report.read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        return {}
    first = next((ln.strip().strip('*').strip() for ln in text.splitlines() if re.search(r'\w', ln)), '')
    if not first.lower().startswith('worker:'):
        return {}
    return {m.group(1).lower(): m.group(2) for m in re.finditer(r'(\w+)=([^\s·]+)', first)}


def substantive(report: Path) -> bool:
    """True when a report's body, after the `worker:` line, cites a `path:line` or holds 200+ characters (ticket 1361)."""
    try:
        text = report.read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        return False
    body = '\n'.join([ln for ln in text.splitlines() if re.search(r'\w', ln)][1:])
    return bool(re.search(r'[\w./-]+\.\w+:\d+', body)) or len(body.strip()) >= 200


def _token(value: str) -> str:
    return re.sub(r'[\s·=:]+', '-', value.strip()) or 'not-stated'


def qualify(model: str, runtime: str) -> str:
    """Provider-qualify a bare model id with the provider that bills it on `runtime`'s door."""
    if '/' in model or model == 'not observed':
        return model
    spec = importlib.util.spec_from_file_location('gaze_seat', Path(__file__).with_name('gaze_seat.py'))
    gaze_seat = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gaze_seat)
    try:
        door = gaze_seat.load_doors(gaze_seat.ROUTES).get(runtime)
    except (OSError, ValueError, KeyError):
        door = None
    provider = gaze_seat.billed_provider(door, model) if door else None
    return f'{provider.lower()}/{model}' if provider else model


def door_family(runtime: str, model: str) -> str:
    """The family that really ran a seat on `runtime`'s own door (ticket 1360), never the plan label.

    The runtime's subagent (else headless) door with one family gives it; else the model's `<provider>/` prefix;
    else `unconfirmed`. Read from skills/route/routes.json launch_doors."""
    try:
        routes = json.loads(Path(__file__).resolve().parent.parent.joinpath('skills/route/routes.json')
                            .read_text(encoding='utf-8'))
        door = routes['launch_doors'][runtime]
        families = (door.get('subagent', {}).get('families') or door.get('headless', {}).get('families') or [])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        families = []
    if len(families) == 1 and not families[0].lower().startswith('any provider'):
        return families[0].lower()
    model = model.strip()
    return model.split('/', 1)[0].lower() if '/' in model else 'unconfirmed'


def launched_seats() -> set[tuple[str, str]] | None:
    """(seat, unit) of every launch line the launchers wrote (ticket 1399); None when the archive is unreadable."""
    try:
        path = launch_line.launches_path()
        if not path.exists():
            return set()
        rows = [json.loads(ln) for ln in path.read_text(encoding='utf-8').splitlines() if ln.strip()]
        return {(str(r['seat']), str(r.get('unit', '-'))) for r in rows}
    except (OSError, ValueError, KeyError, TypeError):
        print('seat_clock: launch archive unreadable; no headless header is trusted', file=sys.stderr)
        return None


def identities(panel: Path, session_runtime: str = '', session_model: str = '') -> list[dict[str, str]]:
    """One identity per worker item of the plan, from the plan and the launcher's header (ticket 1303).

    A non-self report counts as `ran` only when substantive: a `path:line` citation or 200+ characters (ticket 1361)."""
    _, _, _, accepted = _assess(panel)
    session_runtime = session_runtime.strip() or 'not-stated'
    launches = launched_seats()
    unit = launch_line.unit()
    out = []
    for cells in manifest_items(panel):
        name, pin = cells[0], (cells[1].strip() if len(cells) > 1 else '')
        family = planned = cells[2].strip() if len(cells) > 2 else ''
        reason = cells[3] if len(cells) > 3 else ''
        if len(cells) < 3 or family == 'none':
            continue  # free text is no plan item (the plan check fails it); a script is not a worker
        header = worker_header(panel / f'{name}.md')
        door = re.search(r'headless[ ]+(\S+)', reason)
        # a headless header is trusted only when the launcher recorded this seat for this review (1399)
        stamped = any(seat == name and (u == unit or '-' in (u, unit)) for seat, u in launches or ())
        if is_self(cells):
            runtime, model, route = session_runtime, session_model.strip() or 'not observed', 'self'
            family = door_family(runtime, model)  # the session's family, not the label (1360)
        elif header.get('door') == 'headless' and header.get('runtime') and stamped:
            # the launch line is the observed fact; neither the header text alone nor the plan's reason is (1388, 1396, 1399)
            runtime, model, route = header['runtime'], header.get('model') or pin, _token(pin)
            family = header.get('family') or family  # launcher-set: the plan cannot relabel it (1326)
        elif door:
            runtime, model, route = door.group(1).strip('.,;)('), pin, _token(pin)
            if name in accepted:  # a report the launcher did not stamp: its family is unconfirmed (1326)
                route = 'unconfirmed'
        else:
            runtime, model, route = session_runtime, pin, 'subagent'
            family = door_family(runtime, model)  # the door that ran it, not the label (1360)
        status = ('skipped' if reason.strip().lower().startswith('skipped')
                  else 'ran' if name in accepted and (is_self(cells) or substantive(panel / f'{name}.md'))
                  else 'failed')  # a hollow worker report reviewed nothing (1361)
        out.append({'planned': planned, 'seat': name, 'runtime': _token(runtime), 'family': _token(family or header.get('family', '')),
                    'route': route, 'model': qualify(model, runtime) if model else 'not observed',
                    'status': status})
    return out


def format_seat(ident: dict[str, str]) -> str:
    return (f"seat: {ident['seat']} · runtime={ident['runtime']} · family={ident['family']} · "
            f"route={ident['route']} · model={ident['model']} · status: {ident['status']}")


def self_only_problems(items: list[list[str]], no_door: str | None) -> list[str]:
    """Ticket 1287: refuse a plan whose every item is self, unless `--no-door` names the doors tried."""
    if items and all(is_self(item) for item in items) and not (no_door or '').strip():
        return ['every item is self, so the run would be seats: self-only; plan a seat on the '
                'headless door (gaze_seat.py launch), or pass --no-door "<doors tried>"']
    return []


def plan_write(panel: Path, intent: str, method: str, budget: str, spend: str | None,
               items: list[list[str]], no_door: str | None = None) -> list[str]:
    """Write the manifest; return the problems (nothing is written when any)."""
    spec = importlib.util.spec_from_file_location(
        'panel_manifest_check', Path(__file__).with_name('panel-manifest-check.py'))
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    flat = [cell for item in items for cell in item] + [intent, method, budget, spend or '', no_door or '']
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
    refused = self_only_problems(items, no_door)
    if refused:
        return refused
    header = [f'# intent: {intent}', f'# method: {method}', f'# budget: {budget}']
    if spend:
        header.append(f'# spend: {spend}')
    if no_door:
        header.append(f'# no-door: {no_door}')
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
    seats_p = sub.add_parser('seats', help='panel or self-only, from the reports')
    seats_p.add_argument('panel', type=Path)
    ident_p = sub.add_parser('identities', help='the seat: lines, built from the plan and the headers')
    ident_p.add_argument('panel', type=Path)
    ident_p.add_argument('--session-runtime', default=os.environ.get('IDH_SESSION_RUNTIME', ''))
    ident_p.add_argument('--session-model', default=os.environ.get('IDH_SESSION_MODEL', ''))
    write_p = sub.add_parser('plan-write', help='write a validated manifest')
    write_p.add_argument('panel', type=Path)
    write_p.add_argument('--intent', required=True)
    write_p.add_argument('--method', required=True)
    write_p.add_argument('--budget', required=True, help='<n>m')
    write_p.add_argument('--spend')
    write_p.add_argument('--no-door', help='doors tried, when every item is self')
    write_p.add_argument('--item', nargs=4, action='append', default=[],
                         metavar=('NAME', 'MODEL', 'FAMILY', 'REASON'))
    args = parser.parse_args(argv)
    if args.mode == 'plan-write':
        problems = plan_write(args.panel, args.intent, args.method, args.budget, args.spend, args.item,
                              args.no_door)
        for problem in problems:
            print(f'seat_clock: plan refused: {problem}', file=sys.stderr)
        if not problems:
            print(f'plan written: {args.panel}/manifest.txt')
        return 2 if problems else 0
    if args.mode == 'run':
        ok, outcome = run_seat(args.cap, args.out, args.command,
                               launch={'seat': seat_name(args.out)})
        line = f'{seat_name(args.out)}: {outcome}'
        try:
            args.out.with_name(args.out.name + '.status').write_text(line + '\n')
        except OSError:
            pass  # the printed line still names the seat
        print(line)
        return 0 if ok else 1
    if args.mode == 'identities':
        try:
            idents = identities(args.panel, args.session_runtime, args.session_model)
            print('\n'.join(format_seat(i) for i in idents))
            for i in idents:  # a plan label the door contradicts is visible, not silent (1360)
                if i['planned'] not in ('', 'none') and i['family'] != i['planned'].lower():
                    print(f"deviation: {i['seat']}: planned family {i['planned']}, ran as {i['family']}", file=sys.stderr)
        except OSError as error:
            print(f'seat_clock: cannot read {args.panel}/manifest.txt: {error}', file=sys.stderr)
            return 2
        return 0
    if args.mode == 'seats':
        try:
            print(seats(args.panel))
        except OSError as error:
            print(f'seat_clock: cannot read {args.panel}/manifest.txt: {error}', file=sys.stderr)
            return 2
        return 0
    try:
        complete, lines = (plan_check if args.mode == 'plan-check' else roster)(args.panel)
    except OSError as error:
        print(f'seat_clock: cannot read {args.panel}/manifest.txt: {error}', file=sys.stderr)
        return 2
    print('\n'.join(lines))
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
