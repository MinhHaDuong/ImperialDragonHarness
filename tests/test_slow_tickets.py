"""Slow-ticket classification for lair step 16 (ticket 1239): synthetic records, no gh, no waiting."""

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
