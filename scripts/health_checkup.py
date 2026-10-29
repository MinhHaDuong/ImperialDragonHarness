#!/usr/bin/env python3
"""Harness health checkup: KPIs and vital signs into a long-lived journal (ticket 1334).

    python3 scripts/health_checkup.py [--journal PATH] [--dry-run] [--days N]
    python3 scripts/health_checkup.py --plot METRIC[,METRIC...] [--out FILE.png]

The first form measures the harness over the window since the previous journal
record (first record: the last `--days`, default 7; never more than 30) and
appends one JSON object to `health/journal.jsonl`; the terminal shows each
headline figure beside the previous record and the biggest movers. The second
renders the named series from the journal; only it imports matplotlib.

It reads what monitoring already stores and adds no instrumentation:
closed tickets and their PRs (slow_tickets.collect), ticket headers and logs,
`refs/notes/review` (gaze answers, verify-gate verdicts), `refs/notes/gate`
(after-merge records on main), `idh/after-merge.log` under the git common dir,
the text of skills, rules and scripts (stdlib `ast` for complexity), and the
provider's own billing record for each API key. No model call; no estimate:
billed cost is what the provider reports, never tokens times a price list.

Record: `schema`, `ts`, `host`, `commit`, `window`, and a flat `metrics` object
of `name -> {value, unit, source}`. A source that is missing or unreadable
gives `value: null` and a `gap` reason, never 0 and never an omission. Readers
tolerate unknown and missing names, so metrics can be added or retired freely.
Key values are never printed or written: a record names the key's env name only.
"""

import argparse
import ast
import importlib.util
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

SCHEMA = 1
SCRIPTS = Path(__file__).resolve().parent
FIRST_WINDOW_DAYS = 7
MAX_WINDOW_DAYS = 30
OPENROUTER_KEYS = ('OPENROUTER_API_KEY_PI', 'OPENROUTER_API_KEY_IDH')  # skills/route/routes.json
OPENROUTER_URL = 'https://openrouter.ai/api/v1/key'
KEY_FILES = {'OPENROUTER': 'openrouter.env', 'ANTHROPIC': 'anthropic.env', 'OPENAI': 'openai.env'}


def _root():
    return Path(os.environ.get('IDH_ROOT') or SCRIPTS.parent).resolve()


def _load(name):
    """A sibling script, loaded where it lives (hyphenated names included), never copied."""
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_ts(s):
    t = datetime.fromisoformat(s.replace('Z', '+00:00'))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def iso(t):
    return t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def metric(value, unit, source):
    return {'value': value, 'unit': unit, 'source': source}


def gap(unit, source, reason):
    return {'value': None, 'unit': unit, 'source': source, 'gap': reason}


@dataclass
class Context:
    root: Path
    common_dir: Path
    since: datetime | None
    until: datetime | None
    previous: dict | None
    fetch: Callable | None = None
    key: Callable | None = None


def _git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True,
                          check=True, timeout=120).stdout


def guarded(fn, names, ctx):
    """Run one metric group; an exception, or a promised name left out, becomes a gap, never a 0."""
    try:
        got = fn(ctx)
    except Exception as e:  # noqa: BLE001 -- any failure of a source is a gap, named
        reason = f'{type(e).__name__}: {e}'[:200]
        return {n: gap(u, fn.__name__, reason) for n, u in names.items()}
    for n, u in names.items():
        got.setdefault(n, gap(u, fn.__name__, 'source produced no figure'))
    return got


def _quantiles(values):
    if len(values) == 1:
        return values[0], values[0]
    q = statistics.quantiles(values, n=10, method='inclusive')
    return statistics.median(values), q[8]


# --- KPIs -----------------------------------------------------------------

TICKET_SOLVE = {'ticket.solve_median_min': 'min', 'ticket.solve_p90_min': 'min',
                'ticket.solve_recorded': 'tickets', 'ticket.solve_derived': 'tickets',
                'ticket.solve_unknown': 'tickets'}


def ticket_solve(ctx):
    src = 'slow_tickets.collect (duration: lines, else PR open to merge)'
    rows = _load('slow_tickets').collect(str(ctx.root / 'tickets/closed'), ctx.since)
    ctx.closed_prs = [r['pr'] for r in rows if r.get('pr')]
    known = [r['secs'] / 60 for r in rows if r['secs'] is not None]
    out = {
        'ticket.solve_recorded': metric(sum(r['source'].startswith('read') for r in rows), 'tickets', src),
        'ticket.solve_derived': metric(sum(r['source'].startswith('derived') for r in rows), 'tickets', src),
        'ticket.solve_unknown': metric(sum(r['secs'] is None for r in rows), 'tickets', src),
    }
    if known:
        med, p90 = _quantiles(known)
        out['ticket.solve_median_min'] = metric(round(med, 1), 'min', src)
        out['ticket.solve_p90_min'] = metric(round(p90, 1), 'min', src)
    else:
        for n in ('ticket.solve_median_min', 'ticket.solve_p90_min'):
            out[n] = gap('min', src, 'no ticket closed in the window has a known solve time')
    return out


THROUGHPUT = {'tickets.closed': 'tickets', 'tickets.opened': 'tickets', 'tickets.backlog_net': 'tickets',
              'tickets.open_now': 'tickets'}
LOG_EVENT = re.compile(r'^(\d{4}-\d\d-\d\dT\d\d:\d\dZ) \S+ (created|closed)\b', re.M)


def throughput(ctx):
    src = 'ticket logs (created / closed entries) under tickets/'
    tickets = ctx.root / 'tickets'
    opened = closed = 0
    for p in [*tickets.glob('*.erg'), *(tickets / 'closed').glob('*.erg')]:
        events = LOG_EVENT.findall(p.read_text(errors='replace'))
        made = [parse_ts(t) for t, k in events if k == 'created']
        shut = [parse_ts(t) for t, k in events if k == 'closed']
        opened += bool(made) and ctx.since <= made[0] <= ctx.until
        closed += bool(shut) and ctx.since <= shut[-1] <= ctx.until
    return {'tickets.closed': metric(closed, 'tickets', src), 'tickets.opened': metric(opened, 'tickets', src),
            'tickets.backlog_net': metric(opened - closed, 'tickets', src),
            'tickets.open_now': metric(len(list(tickets.glob('*.erg'))), 'tickets', 'tickets/*.erg')}


def _review_entries(root):
    entries = []
    for line in _git(root, 'notes', '--ref=review', 'list').splitlines():
        note = line.split()[0]
        for row in _git(root, 'cat-file', '-p', note).splitlines():
            try:
                entries.append(json.loads(row))
            except ValueError:
                continue
    return entries


def _pr(entry):
    m = re.search(r'pr:(\d+)', entry.get('unit') or '') or re.search(r'-pr-(\d+)-', entry.get('review_id') or '')
    return int(m.group(1)) if m else None


QUALITY = {'quality.first_pass_share': 'ratio', 'quality.reviewed_prs': 'prs', 'quality.rerolled_prs': 'prs'}


def quality(ctx):
    """PRs of the window's closed tickets that carry review notes; first pass = no REROLL or ESCALATE."""
    src = 'refs/notes/review (local) for PRs of tickets closed in the window'
    prs = set(getattr(ctx, 'closed_prs', None) or [])
    if not prs:
        raise LookupError('no PR of a ticket closed in the window (ticket group gave none)')
    bad, seen = set(), set()
    for e in _review_entries(ctx.root):
        pr = _pr(e)
        if pr not in prs:
            continue
        seen.add(pr)
        if e.get('verdict') in ('REROLL', 'ESCALATE') or (e.get('kind') == 'answer' and e.get('result') == 'ESCALATE'):
            bad.add(pr)
    out = {'quality.reviewed_prs': metric(len(seen), 'prs', src), 'quality.rerolled_prs': metric(len(bad), 'prs', src)}
    out['quality.first_pass_share'] = (metric(round(1 - len(bad) / len(seen), 3), 'ratio', src) if seen
                                       else gap('ratio', src, 'no PR of the window carries review notes'))
    return out


MAIN_HEALTH = {'main.after_merge_runs': 'runs', 'main.after_merge_red': 'runs'}
AFTER_LINE = re.compile(r'^(pass|red): after-merge record on ([0-9a-f]{40})', re.M)


def _main_commits(ctx):
    ref = 'origin/main' if subprocess.run(['git', '-C', str(ctx.root), 'rev-parse', '-q', '--verify', 'origin/main'],
                                          capture_output=True).returncode == 0 else 'main'
    return ref, _git(ctx.root, 'rev-list', '--first-parent', f'--since={iso(ctx.since)}',
                     f'--until={iso(ctx.until)}', ref).split()


def main_health(ctx):
    log = Path(ctx.common_dir) / 'idh/after-merge.log'
    src = 'idh/after-merge.log (pass: / red: lines) on main commits of the window'
    if not log.is_file():
        raise FileNotFoundError('idh/after-merge.log not found under the git common dir')
    _, window = _main_commits(ctx)
    window = set(window)
    result = {}
    for kind, sha in AFTER_LINE.findall(log.read_text(errors='replace')):
        if sha in window:
            result[sha] = kind
    return {'main.after_merge_runs': metric(len(result), 'runs', src),
            'main.after_merge_red': metric(sum(k == 'red' for k in result.values()), 'runs', src)}


TIMINGS = {'timing.gaze_median_s': 's', 'timing.gaze_runs': 'runs', 'timing.test_gate_median_s': 's',
           'timing.session_start_s': 's'}
DURATION = re.compile(r'^duration: (?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?\s*$', re.M)
GATE_CHECK = re.compile(r'^check: pytest-guard pass ([\d.]+)s', re.M)


def timings(ctx):
    out = {'timing.session_start_s': gap('s', 'none', 'no store records session-start duration; '
                                         'the checkup adds no instrumentation')}
    src = 'refs/notes/review gaze answers (duration: line)'
    secs = []
    for e in _review_entries(ctx.root):
        if e.get('kind') != 'answer' or not e.get('ts') or not (ctx.since <= parse_ts(e['ts']) <= ctx.until):
            continue
        for h, m, s in DURATION.findall(e.get('text') or ''):
            if h or m or s:
                secs.append(int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0))
    out['timing.gaze_runs'] = metric(len(secs), 'runs', src)
    out['timing.gaze_median_s'] = (metric(statistics.median(secs), 's', src) if secs
                                   else gap('s', src, 'no gaze answer with a duration in the window'))
    gsrc = 'refs/notes/gate after-merge records on main (pytest-guard check)'
    ref, commits = _main_commits(ctx)
    gate = []
    if commits:
        text = _git(ctx.root, 'log', '--no-walk', '--notes=gate', '--format=%N', *commits)
        gate = [float(x) for x in GATE_CHECK.findall(text)]
    out['timing.test_gate_median_s'] = (metric(statistics.median(gate), 's', gsrc) if gate
                                        else gap('s', gsrc, f'no pytest-guard check on {ref} in the window'))
    return out


# --- billed cost ------------------------------------------------------------

def _fetch_openrouter(url, key):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 -- fixed https URL
        return json.load(r)


def _keystore_key(env):
    """The key named `env` from its provider file, via the harness keystore reader. Never printed."""
    path = Path.home() / '.config/keys' / KEY_FILES[env.split('_')[0]]
    try:
        return _load('keystore').keystore_value(path, env)
    except Exception:  # noqa: BLE001 -- the value never travels in the exception; dropped anyway
        return None


def _prev_value(ctx, name):
    m = ((ctx.previous or {}).get('metrics') or {}).get(name) or {}
    return m.get('value')


def billed_cost(ctx):
    """What each key was charged, read from the provider. OpenRouter reports a key's cumulative usage;
    the window is the difference with the previous record. Anthropic and OpenAI need admin keys."""
    fetch, key = ctx.fetch or _fetch_openrouter, ctx.key or _keystore_key
    out, window_total, included = {}, 0.0, []
    for env in OPENROUTER_KEYS:
        src = f'openrouter /api/v1/key usage for {env}'
        cum, win = f'billed.openrouter.{env}.cumulative_usd', f'billed.openrouter.{env}.window_usd'
        k = key(env)
        if not k:
            out[cum] = out[win] = gap('USD', src, f'{env} not held in the keystore')
            continue
        try:
            usage = float(fetch(OPENROUTER_URL, k)['data']['usage'])
        except Exception as e:  # noqa: BLE001 -- name the failure class only, nothing of the request
            code = getattr(e, 'code', '')
            out[cum] = out[win] = gap('USD', src, f'provider read failed: {type(e).__name__} {code}'.strip())
            continue
        finally:
            k = None
        out[cum] = metric(round(usage, 4), 'USD', src)
        prev = _prev_value(ctx, cum)
        if prev is None:
            out[win] = gap('USD', src, 'no earlier cumulative figure; the window starts at the next record')
        elif usage < prev:
            out[win] = gap('USD', src, 'cumulative usage fell since the previous record (key reset or rotated)')
        else:
            out[win] = metric(round(usage - prev, 4), 'USD', src)
            window_total += usage - prev
            included.append(env)
    for prov, env in (('anthropic', 'ANTHROPIC_ADMIN_KEY'), ('openai', 'OPENAI_ADMIN_KEY')):
        reason = (f'{env} held but no reader for its cost endpoint yet' if key(env)
                  else f'cost endpoint needs an admin key ({env}); none held')
        out[f'billed.{prov}.window_usd'] = gap('USD', f'{prov} cost report', reason)
    tsrc = 'sum of provider windows read: ' + (', '.join(included) or 'none')
    out['billed.total.window_usd'] = (metric(round(window_total, 4), 'USD', tsrc) if included
                                      else gap('USD', tsrc, 'no provider window readable'))
    return out


BILLED = {f'billed.openrouter.{e}.{k}': 'USD' for e in OPENROUTER_KEYS for k in ('cumulative_usd', 'window_usd')}
BILLED.update({'billed.anthropic.window_usd': 'USD', 'billed.openai.window_usd': 'USD',
               'billed.total.window_usd': 'USD'})


# --- vital signs -----------------------------------------------------------

def _lines(p):
    return len(p.read_text(errors='replace').splitlines())


def _python_scripts(root):
    for p in sorted((root / 'scripts').iterdir()):
        if not p.is_file():
            continue
        if p.suffix == '.py':
            yield p
        elif not p.suffix:
            with p.open('rb') as f:
                if b'python' in f.readline():
                    yield p


SIZE = {'size.skills.lines_total': 'lines', 'size.skills.ref_lines_total': 'lines',
        'size.rules_resident.lines_total': 'lines', 'size.scripts.lines_total': 'lines'}


def size(ctx):
    root, out = ctx.root, {}
    skills = sorted(p for p in (root / 'skills').glob('*/SKILL.md'))
    s_tot = r_tot = 0
    for p in skills:
        name = p.parent.name
        n = _lines(p)
        refs = sum(_lines(r) for r in (p.parent / 'references').glob('**/*.md'))
        out[f'size.skill.{name}.lines'] = metric(n, 'lines', f'skills/{name}/SKILL.md')
        out[f'size.skill.{name}.ref_lines'] = metric(refs, 'lines', f'skills/{name}/references/**/*.md')
        s_tot, r_tot = s_tot + n, r_tot + refs
    out['size.skills.lines_total'] = metric(s_tot, 'lines', 'skills/*/SKILL.md')
    out['size.skills.ref_lines_total'] = metric(r_tot, 'lines', 'skills/*/references/**/*.md')
    resident_census = _load('resident_census')  # the census owns which rules are resident
    rules = [p for p in sorted((root / 'rules').rglob('*.md')) if resident_census.is_auto_loaded(p)]
    for p in rules:
        out[f'size.rule.{p.relative_to(root / "rules")}.lines'] = metric(_lines(p), 'lines', 'resident_census')
    out['size.rules_resident.lines_total'] = metric(sum(_lines(p) for p in rules), 'lines', 'resident_census')
    tot = 0
    for p in sorted(x for x in (root / 'scripts').iterdir() if x.is_file()):
        n = _lines(p)
        tot += n
        out[f'size.script.{p.name}.lines'] = metric(n, 'lines', f'scripts/{p.name}')
    out['size.scripts.lines_total'] = metric(tot, 'lines', 'scripts/*')
    return out


BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.IfExp, ast.comprehension,
                ast.match_case, ast.ExceptHandler) + ((ast.TryStar,) if hasattr(ast, 'TryStar') else ())


def py_complexity(path):
    """(functions, branch nodes) of one Python file, counted with the stdlib ast."""
    tree = ast.parse(Path(path).read_text(errors='replace'))
    funcs = branches = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            funcs += not isinstance(node, ast.Lambda)
        elif isinstance(node, BRANCH_NODES):
            branches += 1
        elif isinstance(node, ast.BoolOp):
            branches += len(node.values) - 1
        if isinstance(node, ast.comprehension):
            branches += len(node.ifs)
    return funcs, branches


STEP = re.compile(r'^\s*\d+\.\s', re.M)
TABLE_ROW = re.compile(r'^\|(?!\s*:?-{3,})', re.M)
XREF = re.compile(r'(?:skills|rules|references|profiles|agents)/[\w./-]+\.md')
COMPLEXITY = {'complexity.scripts.functions_total': 'functions', 'complexity.scripts.branches_total': 'branches',
              'complexity.skills.steps_total': 'steps', 'complexity.skills.table_rows_total': 'rows',
              'complexity.skills.xrefs_total': 'refs'}


def complexity(ctx):
    root, out, tf, tb = ctx.root, {}, 0, 0
    for p in _python_scripts(root):
        try:
            f, b = py_complexity(p)
        except SyntaxError as e:
            out[f'complexity.script.{p.name}.functions'] = gap('functions', 'ast', f'SyntaxError line {e.lineno}')
            continue
        out[f'complexity.script.{p.name}.functions'] = metric(f, 'functions', 'ast')
        out[f'complexity.script.{p.name}.branches'] = metric(b, 'branches', 'ast')
        tf, tb = tf + f, tb + b
    out['complexity.scripts.functions_total'] = metric(tf, 'functions', 'ast over scripts/ python')
    out['complexity.scripts.branches_total'] = metric(tb, 'branches', 'ast over scripts/ python')
    totals = {'steps': 0, 'table_rows': 0, 'xrefs': 0}
    for p in sorted((root / 'skills').glob('*/SKILL.md')):
        text = p.read_text(errors='replace')
        counts = {'steps': len(STEP.findall(text)), 'table_rows': len(TABLE_ROW.findall(text)),
                  'xrefs': len(XREF.findall(text))}
        for k, v in counts.items():
            out[f'complexity.skill.{p.parent.name}.{k}'] = metric(v, k, f'skills/{p.parent.name}/SKILL.md')
            totals[k] += v
    for k, unit in (('steps', 'steps'), ('table_rows', 'rows'), ('xrefs', 'refs')):
        out[f'complexity.skills.{k}_total'] = metric(totals[k], unit, 'skills/*/SKILL.md')
    return out


GROUPS = ((ticket_solve, TICKET_SOLVE), (throughput, THROUGHPUT), (quality, QUALITY),
          (main_health, MAIN_HEALTH), (timings, TIMINGS), (billed_cost, BILLED),
          (size, SIZE), (complexity, COMPLEXITY))


# --- journal ----------------------------------------------------------------

def read_journal(path):
    out = []
    p = Path(path)
    if not p.is_file():
        return out
    for line in p.read_text().splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and isinstance(rec.get('metrics'), dict):
            out.append(rec)
    return out


def read_series(path, names):
    """name -> [(ts, value or None)] over every record; a record without the name gives None."""
    recs = sorted(read_journal(path), key=lambda r: r.get('ts', ''))
    return {n: [(r.get('ts'), (r['metrics'].get(n) or {}).get('value')) for r in recs] for n in names}


def plot(series, out):
    import matplotlib  # noqa: PLC0415 -- only the plot mode needs it

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt  # noqa: PLC0415

    fig, ax = plt.subplots(figsize=(8, 4))
    for name, points in series.items():
        pts = [(parse_ts(t), v) for t, v in points if t and isinstance(v, (int, float))]
        if pts:
            ax.plot([t for t, _ in pts], [v for _, v in pts], marker='o', label=name)
    ax.set_xlabel('checkup')
    ax.legend(loc='best', fontsize='small')
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, format='png')
    plt.close(fig)


def build_record(metrics, since, until, root):
    try:
        commit = _git(root, 'rev-parse', 'HEAD').strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    return {'schema': SCHEMA, 'ts': iso(until), 'host': socket.gethostname(), 'commit': commit,
            'window': {'since': iso(since), 'until': iso(until)}, 'metrics': metrics}


def _num(m):
    v = (m or {}).get('value')
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def movers(cur, prev, top=3):
    """The `top` metrics with the largest relative change against the previous record."""
    if not prev:
        return []
    changes = []
    for n, m in cur['metrics'].items():
        a, b = _num((prev.get('metrics') or {}).get(n)), _num(m)
        if a is not None and b is not None and a != 0 and a != b:
            changes.append((n, (b - a) / abs(a)))
    return sorted(changes, key=lambda x: -abs(x[1]))[:top]


def _headline(name):
    return not re.match(r'(size|complexity)\.(skill|script|rule)\.', name)


def report(cur, prev):
    pm = (prev or {}).get('metrics') or {}
    w = cur['window']
    lines = [f"health checkup {cur['ts']} on {cur['host']} at {(cur['commit'] or '?')[:12]}, "
             f"window {w['since']} .. {w['until']}", f"{'metric':56} {'now':>12} {'previous':>12}"]
    for n, m in cur['metrics'].items():
        if not _headline(n):
            continue
        now = 'gap' if m.get('value') is None else m['value']
        was = (pm.get(n) or {}).get('value', '-') if prev else '-'
        lines.append(f'{n:56} {now!s:>12} {"gap" if was is None else was!s:>12}')
        if m.get('value') is None:
            lines.append(f'    gap: {m.get("gap")}')
    mv = movers(cur, prev)
    lines.append('biggest movers: ' + (', '.join(f'{n} {c:+.0%}' for n, c in mv) if mv else 'none (no previous record)'))
    return '\n'.join(lines)


def latest(recs):
    return max(recs, key=lambda r: str(r.get('ts', '')), default=None)


def _fetch_main(root):
    """Refresh origin/main so the main-commit window is not cut short by a stale ref. Best effort."""
    try:
        return subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin', 'main'], capture_output=True,
                              timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def checkup(root, journal, days=FIRST_WINDOW_DAYS, now=None):
    now = now or datetime.now(timezone.utc)
    recs = read_journal(journal)
    # Union merges join parallel branches' appends in any order: the previous record is the latest ts.
    prev = latest(recs)
    since = parse_ts(prev['ts']) if prev else now - timedelta(days=days)
    since = max(since, now - timedelta(days=MAX_WINDOW_DAYS))
    common = Path(_git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir').strip())
    fetched = _fetch_main(root)
    ctx = Context(root=root, common_dir=common, since=since, until=now, previous=prev)
    metrics = {}
    for fn, names in GROUPS:
        metrics.update(guarded(fn, names, ctx))
    rec = build_record(metrics, since, now, root)
    rec['window']['main_fetched'] = fetched  # False: main figures may stop at a stale origin/main
    return rec, prev


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--journal', help='journal path (default: <root>/health/journal.jsonl)')
    ap.add_argument('--dry-run', action='store_true', help='measure and report, append nothing')
    ap.add_argument('--days', type=int, default=FIRST_WINDOW_DAYS, help='first-record window in days')
    ap.add_argument('--plot', help='comma-separated metric names to plot from the journal')
    ap.add_argument('--out', default='health-plot.png', help='PNG path for --plot')
    a = ap.parse_args(argv)
    root = _root()
    journal = Path(a.journal) if a.journal else root / 'health/journal.jsonl'
    if a.plot:
        plot(read_series(journal, [n.strip() for n in a.plot.split(',') if n.strip()]), a.out)
        print(f'plot: {a.out}')
        return 0
    rec, prev = checkup(root, journal, days=a.days)
    print(report(rec, prev))
    if not a.dry_run:
        journal.parent.mkdir(parents=True, exist_ok=True)
        with journal.open('a') as f:
            f.write(json.dumps(rec, sort_keys=False, separators=(',', ':')) + '\n')
        print(f'appended: {journal}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
