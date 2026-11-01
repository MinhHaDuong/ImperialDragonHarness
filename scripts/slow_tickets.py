#!/usr/bin/env python3
"""List tickets closed in the last 24 h whose solve time exceeded the threshold (ticket 1239).

    python3 scripts/slow_tickets.py [TICKET_ROOT] [--since YYYY-MM-DD[THH:MM]]

`--since` widens the window (ticket 1334); `collect()` gives every closed ticket
of a window with its solve time and source, for the health checkup.

Solve time, defined once: the sum of the measured `duration:` lines that gaze,
verify-gate and merge post on the ticket's merge request ("read from a record").
Without any, the request's opening to its merge ("derived", an upper bound that
includes queue wait). Without either, unknown, which is listed, never treated as fast.

A close that is not a solve (ticket 1420) has no solve time: won't-do, superseded
or duplicate wording on the Closed line, or a "Tracker" title. Those and the
unknown ones are reported as one summary line each with their ids, never as a
per-ticket /harness-doctor suggestion, so the report neither cries wolf nor
reads as an all-clear it cannot back.
"""
import argparse
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

THRESHOLD_MIN = 30  # the single home of the threshold

DURATION = re.compile(r'^(?:.*?\b)?duration: (?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?\s*$', re.M)
PR_LINK = re.compile(r'^Closed:.*?\bPR\s*#?(\d+)', re.M)
# The close reason's leading word, after an optional date: a solve that merely
# mentions "supersedes 1300" later in the line is still a solve.
NONSOLVE = re.compile(r"\s*(?:\d{4}-\d\d-\d\d\S*\s*[-—:]?\s*)?(?:won'?t[ -]?do|wontfix|supersed|duplicate)", re.I)
CLOSED_LINE = re.compile(r'^Closed:(.*)$', re.M)
TITLE_LINE = re.compile(r'^Title:\s*(.*)$', re.M)


def pr_of(text):
    m = PR_LINK.search(text)
    return int(m.group(1)) if m else None


def nonsolve_of(text):
    """Why this close is not a solve (explicit signals only), else None."""
    m = CLOSED_LINE.search(text)
    if m and NONSOLVE.match(m.group(1)):
        return 'won\'t-do/superseded/duplicate'
    t = TITLE_LINE.search(text)
    if t and re.match(r'(?:tracker|epic)\b', t.group(1).strip(), re.I):
        return 'tracker'
    return None


def _measured(comments):
    total, found = 0, False
    for body in comments or []:
        for h, m, s in DURATION.findall(body):
            if h or m or s:
                total += int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)
                found = True
    return total if found else None


def _parse(t):
    return datetime.fromisoformat(t.replace('Z', '+00:00'))


def _span(created, merged):
    try:
        return (_parse(merged) - _parse(created)).total_seconds()
    except (AttributeError, TypeError, ValueError):
        return None


def solve(r):
    """(seconds, source) of one record: measured durations, else the PR span, else (None, 'unknown')."""
    secs = _measured(r.get('comments'))
    if secs is not None:
        return secs, 'read from a record (duration: comments)'
    secs = _span(r.get('created'), r.get('merged'))
    if secs is not None:
        return secs, 'derived (PR open to merge, upper bound incl. queue wait)'
    return None, 'unknown'


def classify(records, threshold=THRESHOLD_MIN):
    out = []
    for r in records:
        if r.get('nonsolve'):
            out.append({**r, 'minutes': None, 'source': 'non-solve', 'doctor': None})
            continue
        secs, source = solve(r)
        if secs is None:
            out.append({**r, 'minutes': None, 'source': 'unknown', 'doctor': '/harness-doctor'})
            continue
        if secs / 60 <= threshold:
            continue
        ci = r.get('ci_seconds') or 0
        doctor = '/test-doctor' if ci * 2 >= secs else '/harness-doctor'
        out.append({**r, 'minutes': int(secs // 60), 'source': source, 'doctor': doctor, 'secs': secs})
    return out


def render(items):
    lines, unknown, nonsolve = [], [], []
    for i in items:
        if i.get('nonsolve'):
            nonsolve.append(f"{i['ticket']} ({i['nonsolve']})")
            continue
        if i['minutes'] is None:
            unknown.append(str(i['ticket']))
            continue
        pr = f"PR #{i['pr']}" if i.get('pr') else 'no PR'
        dur = f"{i['minutes']}m [{i['source']}]"
        lines.append(f"slow ticket {i['ticket']}: {dur}, {pr}; suggest {i['doctor']} with this as the complaint")
    if nonsolve:
        lines.append(f"closed without a solve, not measured: {', '.join(nonsolve)}")
    if unknown:
        lines.append(f"unknown solve time, could not be measured (not shown fast): {', '.join(unknown)}")
    return '\n'.join(lines)


def _gh_record(ticket, pr):
    rec = {'ticket': ticket, 'pr': pr}
    if pr is None:
        return rec
    # Residue of ticket 1319, kept on raw gh: forge.py has no verb for createdAt, comments and checks of one
    # request, and a missing forge already degrades to an unknown duration (no all-clear is claimed).
    try:  # harness-extension-point: forge read
        j = json.loads(subprocess.run(
            ['gh', 'pr', 'view', str(pr), '--json', 'createdAt,mergedAt,comments,statusCheckRollup'],
            capture_output=True, text=True, timeout=60, check=True).stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return rec
    rec.update(created=j.get('createdAt'), merged=j.get('mergedAt'),
               comments=[c.get('body', '') for c in j.get('comments', [])])
    starts = [c['startedAt'] for c in j.get('statusCheckRollup') or [] if c.get('startedAt', '').startswith('20')]
    ends = [c['completedAt'] for c in j.get('statusCheckRollup') or [] if c.get('completedAt', '').startswith('20')]
    if starts and ends:
        rec['ci_seconds'] = _span(min(starts), max(ends))
    return rec


def _closed_since(root, since):
    """(ticket, pr, nonsolve reason) of every ticket under `root` whose last close falls at or after `since`."""
    out = []
    for p in sorted(Path(root).glob('*.erg')):
        text = p.read_text()
        m = re.findall(r'^(\d{4}-\d\d-\d\dT\d\d:\d\dZ) \S+ closed\b', text, re.M)
        if not m or datetime.fromisoformat(m[-1].replace('Z', '+00:00')) < since:
            continue
        out.append((p.name.split('-')[0], pr_of(text), nonsolve_of(text)))
    return out


def _records(root, since):
    # One gh read per request, run side by side: a week of closes is otherwise minutes of serial waits.
    pairs = _closed_since(root, since)
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(
            lambda t: {'ticket': t[0], 'pr': t[1], 'nonsolve': t[2]} if t[2] else _gh_record(t[0], t[1]), pairs))


def collect(root, since):
    """Every ticket closed since `since`, each with `secs` (None when unknown) and its `source`."""
    out = []
    for r in _records(root, since):
        secs, source = solve(r)
        out.append({**r, 'secs': secs, 'source': source})
    return out


def main(root='tickets/closed', hours=24, since=None):
    since = since or datetime.now(timezone.utc) - timedelta(hours=hours)
    out = render(classify(_records(root, since)))
    if out:
        print(out)


def cli(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('root', nargs='?', default='tickets/closed')
    ap.add_argument('--since', help='window start, ISO date or UTC datetime (default: 24 h ago)')
    a = ap.parse_args(argv)
    since = None
    if a.since:
        since = datetime.fromisoformat(a.since.replace('Z', '+00:00'))
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
    main(a.root, since=since)


if __name__ == '__main__':
    cli()
