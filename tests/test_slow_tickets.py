"""Slow-ticket classification for lair step 15 (ticket 1239): synthetic records, no gh, no waiting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

import slow_tickets as st  # noqa: E402


def rec(minutes, **kw):
    return {'ticket': '1', 'pr': 7, 'created': '2026-10-27T10:00:00Z',
            'merged': f'2026-10-27T{10 + minutes // 60:02d}:{minutes % 60:02d}:00Z', **kw}


def test_29_minutes_is_not_listed_31_is():
    assert st.classify([rec(29)]) == []
    out = st.classify([rec(31)])
    assert len(out) == 1 and out[0]['minutes'] == 31


def test_pr_span_is_labelled_upper_bound_derived():
    out = st.classify([rec(31)])[0]
    assert out['source'].startswith('derived') and 'queue' in out['source']


def test_duration_comments_win_over_pr_span_and_are_read_from_a_record():
    comments = ['verdict APPROVED\nduration: 12m30s', 'merge abc: duration: 120s', 'duration: 20m00s']
    out = st.classify([rec(300, comments=comments)])[0]
    assert out['minutes'] == 34 and out['source'].startswith('read from a record')
    # the long PR span alone would say 300; the measured sum says 34.5
    assert st.classify([rec(300, comments=['duration: 5m00s'])]) == []


def test_not_measured_comments_do_not_count_as_zero():
    out = st.classify([rec(31, comments=['duration: not measured'])])[0]
    assert out['source'].startswith('derived')


def test_unreadable_duration_is_listed_unknown_never_fast():
    for r in ({'ticket': '2', 'pr': None}, {'ticket': '3', 'pr': 9, 'created': 'x', 'merged': None},
              {'ticket': '4', 'pr': 9, 'created': '2026-10-27T10:00:00Z', 'merged': 'garbage'}):
        out = st.classify([r])
        assert len(out) == 1 and out[0]['minutes'] is None and 'unknown' in st.render(out)


def test_routing_at_half_ci_boundary():
    assert st.classify([rec(40, ci_seconds=1199)])[0]['doctor'] == '/harness-doctor'
    assert st.classify([rec(40, ci_seconds=1200)])[0]['doctor'] == '/test-doctor'


def test_render_is_a_complaint_and_a_suggestion():
    line = st.render(st.classify([rec(31, ci_seconds=1800)]))
    assert 'PR #7' in line and '31m' in line and '/test-doctor' in line


def test_closed_ticket_pr_link_spellings():
    for text in ('Closed: autoclosed — PR #12', 'Closed: Merged PR #12', 'Closed: done — PR #12 merged',
                 'Closed: merged — PR #12'):
        assert st.pr_of(text) == 12
    assert st.pr_of('Closed: done') is None


def _ticket(root, num, closed_at, pr):
    (root / f'{num}-t.erg').write_text(
        f'%erg 0.1\nTitle: t\nCreated: 2026-10-01\nClosed: autoclosed — PR #{pr}\n\n--- log ---\n'
        f'2026-10-01T08:00Z claude created\n{closed_at} reviewer closed — autoclosed — PR #{pr}\n')


def _fake_gh(ticket, pr):
    return {'ticket': ticket, 'pr': pr, 'created': '2026-10-27T10:00:00Z', 'merged': '2026-10-27T11:00:00Z'}


def test_default_output_unchanged_and_since_widens_the_window(tmp_path, monkeypatch, capsys):
    """The bare call keeps its 24 h window and its line; --since reaches back further (ticket 1334)."""
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%MZ')
    old = (now - timedelta(days=5)).strftime('%Y-%m-%dT%H:%MZ')
    _ticket(tmp_path, '0001', recent, 11)
    _ticket(tmp_path, '0002', old, 12)
    monkeypatch.setattr(st, '_gh_record', _fake_gh)
    st.main(str(tmp_path))
    assert capsys.readouterr().out == (
        'slow ticket 0001: 60m [derived (PR open to merge, upper bound incl. queue wait)], PR #11; '
        'suggest /harness-doctor with this as the complaint\n')
    st.cli([str(tmp_path), '--since', (now - timedelta(days=7)).strftime('%Y-%m-%d')])
    out = capsys.readouterr().out
    assert 'slow ticket 0001' in out and 'slow ticket 0002' in out


def test_collect_returns_every_closed_ticket_with_solve_time_and_source(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    _ticket(tmp_path, '0001', (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%MZ'), 11)
    monkeypatch.setattr(st, '_gh_record', lambda t, pr: {**_fake_gh(t, pr), 'merged': '2026-10-27T10:05:00Z'})
    got = st.collect(str(tmp_path), now - timedelta(days=1))
    assert [(r['ticket'], r['secs'], r['source'].split(' ')[0]) for r in got] == [('0001', 300.0, 'derived')]


def test_pr_link_accepts_pr_with_or_without_hash():
    assert st.pr_of('Closed: all met: PR 2120 merged') == 2120
    assert st.pr_of('Closed: fixes PR 2097 (x), 2102') == 2097
    assert st.pr_of('Closed: done') is None


def test_nonsolve_closes_are_summarised_not_suggested():
    assert st.nonsolve_of('Title: x\nClosed: won\'t do — author keeps 1126\n') is not None
    assert st.nonsolve_of('Title: Tracker: data\nClosed: done\n') == 'tracker'
    assert st.nonsolve_of('Title: x\nClosed: PR #3 merged\n') is None
    recs = [{'ticket': '8', 'pr': 5, 'nonsolve': 'tracker'}, {'ticket': '9', 'pr': None}, rec(31, ticket='7')]
    lines = st.render(st.classify(recs)).splitlines()
    assert len(lines) == 3
    assert lines[0].startswith('slow ticket 7')
    assert '8 (tracker)' in lines[1] and '/harness-doctor' not in lines[1]
    assert lines[2].endswith(': 9') and 'unknown' in lines[2] and '/harness-doctor' not in lines[2]
