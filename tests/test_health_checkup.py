"""Harness health checkup (ticket 1334): journal shape, gaps, reader and plot. No network, no gh."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

import health_checkup as hc  # noqa: E402
import pytest  # noqa: E402


def _rec(ts, metrics):
    return {'schema': 1, 'ts': ts, 'host': 'h', 'commit': 'c', 'window': {}, 'metrics': metrics}


def _journal(tmp_path):
    p = tmp_path / 'journal.jsonl'
    rows = [
        _rec('2026-10-01T00:00:00Z', {'ticket.solve_median_min': {'value': 20, 'unit': 'min', 'source': 's'}}),
        _rec('2026-10-08T00:00:00Z', {'ticket.solve_median_min': {'value': None, 'unit': 'min', 'source': 's',
                                                                  'gap': 'no source'},
                                      'retired.name': {'value': 3, 'unit': 'n', 'source': 's'}}),
        _rec('2026-10-15T00:00:00Z', {'ticket.solve_median_min': {'value': 30, 'unit': 'min', 'source': 's'},
                                      'brand.new': {'value': 1.5, 'unit': 'x', 'source': 's'}}),
    ]
    p.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    return p


def test_read_series_spans_records_with_differing_names(tmp_path):
    s = hc.read_series(_journal(tmp_path), ['ticket.solve_median_min', 'brand.new', 'retired.name'])
    assert [v for _, v in s['ticket.solve_median_min']] == [20, None, 30]
    assert [v for _, v in s['brand.new']] == [None, None, 1.5]
    assert [v for _, v in s['retired.name']] == [None, 3, None]


@pytest.mark.slow  # matplotlib is a heavy import (coding-python.md test tiers)
def test_plot_renders_a_series_spanning_differing_records(tmp_path):
    out = tmp_path / 'p.png'
    hc.plot(hc.read_series(_journal(tmp_path), ['ticket.solve_median_min', 'brand.new']), out)
    assert out.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'


def test_a_raising_source_yields_null_with_a_gap():
    def broken(ctx):
        raise FileNotFoundError('after-merge.log')
    got = hc.guarded(broken, {'main.after_merge_red': 'runs'}, ctx=None)
    m = got['main.after_merge_red']
    assert m['value'] is None and m['gap'] and m['unit'] == 'runs'


def test_a_missing_source_file_yields_null_with_a_gap(tmp_path):
    ctx = hc.Context(root=tmp_path, common_dir=tmp_path, since=hc.parse_ts('2026-10-01T00:00:00Z'),
                     until=hc.parse_ts('2026-10-08T00:00:00Z'), previous=None)
    got = hc.guarded(hc.main_health, hc.MAIN_HEALTH, ctx)
    assert got['main.after_merge_red']['value'] is None
    assert 'after-merge.log' in got['main.after_merge_red']['gap']


def test_billed_cost_is_the_provider_record_and_no_key_reaches_the_record():
    secret = 'sk-or-v1-THISMUSTNEVERAPPEAR'
    calls = []

    def fetch(url, key):
        calls.append(url)
        assert key == secret
        return {'data': {'usage': 12.5}}

    prev = _rec('2026-10-01T00:00:00Z', {
        'billed.openrouter.OPENROUTER_API_KEY_PI.cumulative_usd': {'value': 10.0, 'unit': 'USD', 'source': 's'}})
    got = hc.billed_cost(hc.Context(root=Path('.'), common_dir=Path('.'), since=None, until=None, previous=prev,
                                    fetch=fetch, key=lambda env: secret))
    assert got['billed.openrouter.OPENROUTER_API_KEY_PI.window_usd']['value'] == 2.5
    assert got['billed.openrouter.OPENROUTER_API_KEY_IDH.window_usd']['value'] is None  # no earlier figure
    assert got['billed.anthropic.window_usd']['value'] is None and got['billed.anthropic.window_usd']['gap']
    assert got['billed.openai.window_usd']['value'] is None
    assert secret not in json.dumps(got)
    assert all('openrouter.ai' in u for u in calls)


def test_billed_cost_gap_when_key_is_absent():
    got = hc.billed_cost(hc.Context(root=Path('.'), common_dir=Path('.'), since=None, until=None, previous=None,
                                    fetch=lambda u, k: {}, key=lambda env: None))
    m = got['billed.openrouter.OPENROUTER_API_KEY_PI.cumulative_usd']
    assert m['value'] is None and 'not held' in m['gap']


def test_record_shape_and_movers(tmp_path):
    rec = hc.build_record({'a': {'value': 2, 'unit': 'n', 'source': 's'}}, hc.parse_ts('2026-10-01T00:00:00Z'),
                          hc.parse_ts('2026-10-08T00:00:00Z'), root=tmp_path)
    assert set(rec) == {'schema', 'ts', 'host', 'commit', 'window', 'metrics'}
    prev = _rec('x', {'a': {'value': 1}, 'b': {'value': 10}, 'c': {'value': None}})
    cur = _rec('y', {'a': {'value': 4}, 'b': {'value': 11}, 'c': {'value': 5}})
    assert [n for n, _ in hc.movers(cur, prev)][:2] == ['a', 'b']


def test_complexity_counts_functions_and_branches(tmp_path):
    f = tmp_path / 'x.py'
    f.write_text('def a(x):\n    if x:\n        return [i for i in x if i]\n    return 0\n\nasync def b():\n'
                 '    while True:\n        pass\n')
    assert hc.py_complexity(f) == (2, 4)  # if, comprehension, its if, while
