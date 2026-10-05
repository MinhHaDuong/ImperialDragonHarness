"""Hand-counted game/anchor evidence for the project read surfaces."""

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / 'scripts' / 'attribution_query.py'


def record(pr, attempts, events=(), version='v1', writer='w1'):
    lines = ['kind: review-attribution', f'pr: {pr} · merged 2026-10-05 · project: test',
             f'writer: runtime=native · model=p/writer · model-version={writer} · effort=standard']
    for seat, status, findings in attempts:
        lines.append(f'reviewer: seat={seat} · runtime=native · model=p/reviewer · model-version={version} · status: {status}')
        for key, adopted in findings:
            lines.append(f'  finding: verifiable · {key} · adopted: {"yes" if adopted else "no"}')
    lines += [f'defect-confirmed: {key} · source: post-merge-fix · pr: 900' for key in events]
    return '\n'.join(lines) + '\n'


def dataset(tmp_path):
    journal = tmp_path / 'memory/journal/2026'
    journal.mkdir(parents=True)
    games = [
        record(1, [('A','ran',[('x:1',True),('z:3',True),('noise:1',False)]),
                   ('A','ran',[('x:1',True)]), ('B','ran',[('x:1',False),('z:3',False),('noise:1',False)]),
                   ('C','ran',[('y:2',True)])]),
        record(2, [('A','ran',[('x:1',False)]),('B','ran',[('x:1',False)]),('C','ran',[])], ['x:1']),
        record(3, [('A','ran',[]),('B','ran',[]),('C','ran',[('y:2',True)])]),
        record(4, [('A','ran',[]),('B','ran',[]),('C','ran',[]),('D','ran',[('third:4',True)])]),
        record(5, [('A','ran',[]),('B','ran',[]),('C','ran',[])]),  # clean, excluded
        record(6, [('A','failed',[]),('B','ran',[('x:1',True)]),('C','skipped',[])]),
        record(7, [('A','ran',[('x:1',True)]),('B','ran',[])], version='v2'),
        record(8, [('A','ran',[('x:1',True)]),('B','ran',[])], writer='w2'),
    ]
    for pr, text in enumerate(games, 1):
        (journal / f'2026-10-05-review-attribution-pr{pr}.md').write_text(text)
    return journal


def cli(root, *args):
    return subprocess.run([sys.executable,str(QUERY),str(root),*args], text=True, capture_output=True, env=child_env())


@pytest.mark.integration
def test_cli_hand_counted_games_and_complementary_anchors(tmp_path):
    dataset(tmp_path)
    result = cli(tmp_path, '--json')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['records']['valid'] == 8
    scores = [s for s in data['scores'] if s['writer']['model-version']=='w1' and s['identity']['model-version']=='v1']
    a = next(s for s in scores if s['identity']['seat']=='A')
    assert a['attempts'] == {'ran':6,'failed':1,'skipped':0,'attempted':7}
    assert (a['catch']['successes'],a['catch']['trials']) == (2,4)
    assert (a['run_failure']['successes'],a['run_failure']['trials']) == (1,7)
    assert (a['nonconfirmed_finding_share_proxy']['successes'],a['nonconfirmed_finding_share_proxy']['trials']) == (1,5)
    pairs = [p for p in data['pairs'] if p['writer']['model-version']=='w1' and p['a']['model-version']=='v1']
    ab = next(p for p in pairs if (p['a']['seat'],p['b']['seat'])==('A','B'))
    ac = next(p for p in pairs if (p['a']['seat'],p['b']['seat'])==('A','C'))
    assert ab['cells'] == {'both':2,'unique_a':0,'unique_b':0,'neither':2}
    assert ac['cells'] == {'both':1,'unique_a':1,'unique_b':1,'neither':1}
    assert ab['unique_b_anchors'] == 0
    assert ac['unique_b_anchors'] == 2
    assert (ac['marginal_b_given_a']['successes'],ac['marginal_b_given_a']['trials']) == (2,4)
    assert ab['confirmed_anchor_jaccard'] == {'intersection':3,'union':3,'value':1.0}
    assert ac['confirmed_anchor_jaccard']['value'] == 0.0
    assert ab['shared_nonconfirmed_anchor_proxy']['successes'] == 1
    assert all(p['a']['seat']!='writer' and p['b']['seat']!='writer' for p in data['pairs'])
    assert len([s for s in data['scores'] if s['identity']['seat']=='A']) == 3


@pytest.mark.integration
def test_malformed_duplicate_encrypted_and_empty(tmp_path):
    journal = dataset(tmp_path)
    (journal/'2026-10-06-review-attribution-pr1.md').write_text((journal/'2026-10-05-review-attribution-pr1.md').read_text())
    (journal/'2026-10-05-review-attribution-pr9.md').write_text('kind: review-attribution\npr: broken\n')
    (journal/'2026-10-05-review-attribution-pr10.md.age').write_bytes(b'encrypted')
    result = cli(tmp_path,'--json')
    data = json.loads(result.stdout)
    assert data['records'] == {'valid':7,'malformed':1,'ambiguous_prs':[1],'ambiguous_records':2,'encrypted_unavailable':1}
    assert 'WARN' in result.stderr and 'line 2' in result.stderr and 'ambiguous PR 1' in result.stderr
    empty = cli(tmp_path/'absent','--json')
    assert json.loads(empty.stdout)['scores'] == []
    assert 'no attribution records' in empty.stderr


def load_query():
    spec = importlib.util.spec_from_file_location('scripts.attribution_query',QUERY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.slow
def test_jeffreys_analytic_golden_symmetry_and_extremes():
    rate = load_query().rate
    prior = rate(0,0)['interval90']
    assert prior == pytest.approx([math.sin(math.pi*.05/2)**2,math.sin(math.pi*.95/2)**2])
    # Independently pinned Jeffreys posterior Beta(1.5, 9.5) quantiles.
    assert rate(1,10)['interval90'] == pytest.approx([0.01789198805574782,0.3305628032601345],abs=1e-12)
    low, high = rate(0,10000)['interval90']
    mirror = rate(10000,10000)['interval90']
    assert 0 < low < high < .001
    assert mirror == pytest.approx([1-high,1-low],abs=1e-12)
    assert rate(7,20)['interval90'] == pytest.approx([1-x for x in reversed(rate(13,20)['interval90'])])


@pytest.mark.integration
def test_explicit_merge_coverage_does_not_accept_ambiguous_records(tmp_path):
    def git(*args):
        result = subprocess.run(['git','-C',str(tmp_path),*args],text=True,capture_output=True,check=True,env=child_env())
        return result.stdout.strip()

    journal = dataset(tmp_path)
    (journal/'2026-10-06-review-attribution-pr1.md').write_text((journal/'2026-10-05-review-attribution-pr1.md').read_text())
    git('init','-b','main')
    git('config','user.name','Test')
    git('config','user.email','test@example.com')
    git('config','commit.gpgsign','false')
    git('add','.')
    git('commit','-m','base')
    base = git('rev-parse','HEAD')
    for pr in (1,2,99):
        git('switch','-c',f'branch-{pr}')
        (tmp_path/f'file-{pr}').write_text(str(pr))
        git('add','.')
        git('commit','-m','change')
        git('switch','main')
        git('merge','--no-ff',f'branch-{pr}','-m',f'Merge pull request #{pr} from owner/branch-{pr}')
    data = json.loads(cli(tmp_path,'--json','--since',base,'--until','main').stdout)
    assert [(merge['pr'],merge['attribution']) for merge in data['coverage']] == [(1,'unavailable'),(2,'available'),(99,'missing')]
    assert data['coverage'][-1]['merge_sha'] == git('rev-parse','main')
    assert 'coverage' not in json.loads(cli(tmp_path,'--json').stdout)


@pytest.mark.integration
def test_readable_table_prior_only_and_proxy_labels(tmp_path):
    journal = tmp_path/'memory/journal/2026'
    journal.mkdir(parents=True)
    (journal/'2026-10-05-review-attribution-pr1.md').write_text(record(1,[('skip','skipped',[])]))
    result = cli(tmp_path)
    assert result.returncode == 0
    assert '1/0/0/1' in result.stdout
    assert result.stdout.count('prior-only') == 3
    assert 'failed/(ran+failed)' in result.stdout
    assert 'proxy' in result.stdout and 'upper bound' in result.stdout
