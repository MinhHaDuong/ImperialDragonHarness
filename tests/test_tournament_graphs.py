import importlib.util
from pathlib import Path
from scipy.stats import wilcoxon, PermutationMethod

spec = importlib.util.spec_from_file_location('graphs', Path(__file__).parents[1] / 'scripts/tournament-graphs.py')
graphs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graphs)


def test_exact_wilcoxon_with_ties_and_zeros_matches_scipy():
    differences = [0, 1, 1, 2, 3, -2, 4, 5, 1, 2]
    p, direction = graphs.signed_rank(differences)
    reference = wilcoxon(differences, method=PermutationMethod(n_resamples=float('inf')))
    assert abs(p - reference.pvalue) < 1e-12
    assert direction == 1
    assert graphs.signed_rank([0]*10) == (1, 0)


def test_reduce_retains_reachability_without_inventing_edges():
    edges = {('a','b'), ('b','c'), ('a','c'), ('c','d'), ('a','d')}
    reduced, _ = graphs.reduce_edges('abcd', edges)
    assert reduced == {('a','b'), ('b','c'), ('c','d')}
    for a in 'abcd':
        for b in 'abcd':
            assert graphs.reachable(a,b,edges) == graphs.reachable(a,b,reduced)


def test_cycles_preserve_internal_evidence():
    edges = {('a','b'), ('b','a'), ('a','c'), ('c','d'), ('b','d')}
    reduced, _ = graphs.reduce_edges('abcd', edges)
    assert {('a','b'), ('b','a')} <= reduced
    for a in 'abcd':
        for b in 'abcd':
            assert graphs.reachable(a,b,edges) == graphs.reachable(a,b,reduced)


def test_holm_adjustment():
    rows = [{'p':.001}, {'p':.02}, {'p':.03}]
    graphs.holm(rows)
    assert [r['p_holm'] for r in rows] == [.003,.04,.04]


def test_pareto_uses_axis_direction_and_excludes_provisional():
    arms = {
        'a': {'final': True, 'quality_median': 20, 'cost_usd_median': 1},
        'b': {'final': True, 'quality_median': 25, 'cost_usd_median': 2},
        'c': {'final': True, 'quality_median': 19, 'cost_usd_median': 2},
        'd': {'final': False, 'quality_median': 30, 'cost_usd_median': 0},
    }
    assert graphs.pareto_xy(arms, 'cost_usd_median', 'quality_median') == {'a','b'}


def test_pareto_rejects_unusable_quality_even_on_speed_cost():
    arms = {
        'bad': {'final': True, 'quality_median': 14.99, 'cost_usd_median': .01, 'seconds_median': 1},
        'usable': {'final': True, 'quality_median': 15, 'cost_usd_median': 1, 'seconds_median': 100},
    }
    assert graphs.pareto_xy(arms, 'cost_usd_median', 'seconds_median') == {'usable'}


def test_total_cost_sums_per_ticket_before_median():
    legs = {
        '1': {'cost_usd': 0, 'seconds': 7200},
        '2': {'cost_usd': 1, 'seconds': 3600},
        '3': {'cost_usd': 100, 'seconds': 0},
    }
    assert graphs.total_cost_median(legs, 1) == 2
