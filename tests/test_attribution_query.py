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
    assert data['records'] == {'valid':7,'runtime_masked':0,'model_attributable':7,'malformed':1,'ambiguous_prs':[1],'ambiguous_records':2,'encrypted_unavailable':1,'unsafe_unavailable':0}
    assert 'WARN' in result.stderr and 'line 2' in result.stderr and 'ambiguous PR 1' in result.stderr
    empty = cli(tmp_path/'absent','--json')
    assert json.loads(empty.stdout)['scores'] == []
    assert 'no attribution records' in empty.stderr


def load_query(monkeypatch):
    # The console pytest entry point does not add the repository root.
    # Limit package-path establishment to this test and restore it afterwards.
    monkeypatch.syspath_prepend(str(ROOT))
    spec = importlib.util.spec_from_file_location('scripts.attribution_query',QUERY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.slow
def test_jeffreys_analytic_golden_symmetry_and_extremes(monkeypatch):
    rate = load_query(monkeypatch).rate
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
@pytest.mark.parametrize('sibling', ['valid', 'malformed', 'encrypted', 'header-mismatch', 'private-only', 'private-sibling'])
def test_explicit_merge_coverage_does_not_accept_ambiguous_records(tmp_path, sibling):
    def git(*args):
        result = subprocess.run(['git','-C',str(tmp_path),*args],text=True,capture_output=True,check=True,env=child_env())
        return result.stdout.strip()

    journal = dataset(tmp_path)
    duplicate = (journal/'2026-10-05-review-attribution-pr1.md').read_text()
    if sibling.startswith('private-'):
        (journal/'2026-10-06-review-attribution-pr1.age').write_bytes(b'\xffciphertext-stub')
        if sibling == 'private-only':
            (journal/'2026-10-05-review-attribution-pr1.md').unlink()
    elif sibling == 'encrypted':
        (journal/'2026-10-06-review-attribution-pr1.md.age').write_bytes(b'encrypted')
    else:
        if sibling == 'malformed':
            duplicate += 'reviewer: malformed\n'
        elif sibling == 'header-mismatch':
            duplicate = duplicate.replace('pr: 1 ·', 'pr: 2 ·')
        (journal/'2026-10-06-review-attribution-pr1.md').write_text(duplicate)
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
    assert [(merge['pr'],merge['attribution']) for merge in data['coverage']] == [(1,'unavailable'),(2,'unavailable' if sibling == 'header-mismatch' else 'available'),(99,'missing')]
    if sibling.startswith('private-'):
        assert data['records']['encrypted_unavailable'] == 1
        assert data['records']['valid'] == 7
        assert data['records']['ambiguous_prs'] == ([1] if sibling == 'private-sibling' else [])
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


@pytest.mark.integration
@pytest.mark.parametrize('sibling', ['malformed', 'encrypted', 'header-mismatch'])
def test_invalid_sibling_reserves_pr_and_cannot_receive_credit(tmp_path, sibling):
    journal = dataset(tmp_path)
    source = journal/'2026-10-05-review-attribution-pr1.md'
    target = journal/('2026-10-06-review-attribution-pr1.md.age' if sibling == 'encrypted'
                      else '2026-10-06-review-attribution-pr1.md')
    if sibling == 'encrypted':
        target.write_bytes(b'encrypted')
    elif sibling == 'malformed':
        target.write_text(source.read_text()+'reviewer: malformed\n')
    else:
        target.write_text(source.read_text().replace('pr: 1 ·','pr: 2 ·'))
    result = cli(tmp_path,'--json')
    data = json.loads(result.stdout)
    assert 1 in data['records']['ambiguous_prs']
    assert data['records']['valid'] == (6 if sibling == 'header-mismatch' else 7)
    assert 'ambiguous PR 1' in result.stderr
    a = next(s for s in data['scores'] if s['identity']['seat']=='A' and
             s['identity']['model-version']=='v1' and s['writer']['model-version']=='w1')
    assert a['catch']['trials'] == (2 if sibling == 'header-mismatch' else 3)
    assert a['catch']['successes'] == (0 if sibling == 'header-mismatch' else 1)


@pytest.mark.integration
@pytest.mark.parametrize('boundary', ['outside-record', 'internal-record', 'journal-root', 'year-directory'])
def test_symlink_components_are_unavailable_without_reading_target(tmp_path, boundary):
    project = tmp_path/'project'
    journal = project/'memory/journal/2026'
    journal.mkdir(parents=True)
    outside = tmp_path/'outside'
    outside.mkdir()
    target = outside/'record.md'
    target.write_text(record(1,[('outside-seat','ran',[('x:1',True)])]))
    entry = journal/'2026-10-05-review-attribution-pr1.md'
    if boundary == 'outside-record':
        entry.symlink_to(target)
    elif boundary == 'internal-record':
        internal = journal/'ordinary-note.md'
        internal.write_text(target.read_text())
        entry.symlink_to(internal)
    elif boundary == 'journal-root':
        journal.rmdir()
        journal.parent.rmdir()
        (outside/'2026-10-05-review-attribution-pr1.md').write_text(target.read_text())
        (project/'memory/journal').symlink_to(outside, target_is_directory=True)
    else:
        journal.rmdir()
        (outside/'2026-10-05-review-attribution-pr1.md').write_text(target.read_text())
        journal.symlink_to(outside, target_is_directory=True)
    result = cli(project,'--json')
    data = json.loads(result.stdout)
    assert data['scores'] == [] and data['records']['valid'] == 0
    assert data['records']['unsafe_unavailable'] == 1
    assert 'symlink' in result.stderr and 'WARN' in result.stderr


@pytest.mark.integration
@pytest.mark.parametrize('unique_seat', ['A', 'B'])
def test_both_directional_marginals_survive_pair_sorting(tmp_path, unique_seat):
    journal = tmp_path/'memory/journal/2026'
    journal.mkdir(parents=True)
    attempts = [(seat, 'ran', [('x:1', True)] + ([('y:2', True)] if seat == unique_seat else []))
                for seat in ('A', 'B')]
    (journal/'2026-10-05-review-attribution-pr1.md').write_text(record(1, attempts))
    result = cli(tmp_path, '--json')
    assert result.returncode == 0, result.stderr
    pair = json.loads(result.stdout)['pairs'][0]
    assert (pair['a']['seat'], pair['b']['seat']) == ('A', 'B')
    assert pair['cells'] == {'both':1, 'unique_a':0, 'unique_b':0, 'neither':0}
    assert pair['confirmed_anchor_jaccard'] == {'intersection':1, 'union':2, 'value':.5}
    assert pair['unique_a_anchors'] == (1 if unique_seat == 'A' else 0)
    assert pair['unique_b_anchors'] == (1 if unique_seat == 'B' else 0)
    assert (pair['marginal_a_given_b']['successes'], pair['marginal_a_given_b']['trials']) == (int(unique_seat == 'A'), 1)
    assert (pair['marginal_b_given_a']['successes'], pair['marginal_b_given_a']['trials']) == (int(unique_seat == 'B'), 1)
    readable = cli(tmp_path)
    assert readable.returncode == 0
    header = next(line for line in readable.stdout.splitlines() if 'both/unique-A/unique-B/neither' in line).split(' | ')
    row = next(line for line in readable.stdout.splitlines() if ' | seat=A,' in line and ' | seat=B,' in line).split(' | ')
    fields = dict(zip(header, row))
    assert fields['both/unique-A/unique-B/neither'] == '1/0/0/0'
    assert fields['unique-A anchors'] == str(int(unique_seat == 'A'))
    assert fields['unique-B anchors'] == str(int(unique_seat == 'B'))
    assert fields['marginal A given B'].startswith(f'{int(unique_seat == "A")}/1 [')
    assert fields['marginal B given A'].startswith(f'{int(unique_seat == "B")}/1 [')


@pytest.mark.integration
@pytest.mark.parametrize('public_sibling', [False, True])
def test_actual_private_capture_basename_is_visible_unavailable(tmp_path, public_sibling):
    journal = tmp_path/'memory/journal/2026'
    journal.mkdir(parents=True)
    # memory-capture.sh appends .age directly to its extensionless dated slug.
    (journal/'2026-10-05-review-attribution-pr12.age').write_bytes(b'\xffciphertext-stub')
    if public_sibling:
        (journal/'2026-10-06-review-attribution-pr12.md').write_text(
            record(12, [('A', 'ran', [('x:1', True)])]))
    result = cli(tmp_path, '--json')
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['records']['encrypted_unavailable'] == 1
    assert data['records']['malformed'] == 0
    assert data['records']['valid'] == 0 and data['scores'] == []
    assert data['records']['ambiguous_prs'] == ([12] if public_sibling else [])
    assert data['records']['ambiguous_records'] == (2 if public_sibling else 0)
    assert 'pr12.age' in result.stderr and 'encrypted attribution unavailable' in result.stderr
    readable = cli(tmp_path)
    assert '"encrypted_unavailable": 1' in readable.stdout
    assert 'no decryption attempted' in readable.stderr


@pytest.mark.integration
@pytest.mark.parametrize('masked_identity', ['writer', 'reviewer'])
def test_mask_excludes_whole_game_without_affecting_known_estimates(tmp_path, masked_identity):
    journal = dataset(tmp_path)
    before = json.loads(cli(tmp_path, '--json').stdout)
    text = record(9, [('A', 'ran', [('x:1', True)]), ('B', 'ran', [('new:2', True)])])
    target = 'model=p/writer · model-version=w1' if masked_identity == 'writer' else 'model=p/reviewer · model-version=v1'
    text = text.replace(target, 'model-state=runtime-masked · model-evidence=evidence.md:1', 1)
    (journal / '2026-10-05-review-attribution-pr9.md').write_text(text)
    after = json.loads(cli(tmp_path, '--json').stdout)
    assert after['scores'] == before['scores']
    assert after['pairs'] == before['pairs']
    assert after['records']['valid'] == 9
    assert after['records']['runtime_masked'] == 1
    assert after['records']['model_attributable'] == 8


def test_masked_range_coverage_is_distinct(tmp_path, monkeypatch, caplog):
    query = load_query(monkeypatch)
    text = record(1, [('A', 'ran', [])]).replace(
        'model=p/writer · model-version=w1',
        'model-state=runtime-masked · model-evidence=evidence.md:1')
    response = subprocess.CompletedProcess([], 0, json.dumps({'pr': 1, 'merge_sha': 'abc'}) + '\n', '')
    monkeypatch.setattr(query.subprocess, 'run', lambda *args, **kwargs: response)
    merges = query.coverage(tmp_path, 'base', 'HEAD', [query.parse_record(text)], set())
    assert merges[0]['attribution'] == 'runtime-masked'
    assert 'runtime-masked' in caplog.text


def test_pr1209_reused_contexts_preserve_attempts_without_self_pairs(monkeypatch):
    query = load_query(monkeypatch)
    capture = query.parse_record(
        (ROOT / 'memory/journal/2026/2026-10-06-review-attribution-pr1209.md').read_text())
    assert len(capture['reviewers']) == 14
    attempts = query.game_attempts(capture)
    assert len(attempts) == 7
    expected = {'correctness': 4, 'consistency': 2, 'scope': 1, 'red-team': 2,
                'doc-propagation': 2, 'portable-simplification': 2, 'criterion-gate': 1}
    assert {identity[0]: item['attempts']['ran'] for identity, item in attempts.items()} == expected
    data = query.derive([capture])
    assert len(data['scores']) == 7
    assert sum(score['attempts']['ran'] for score in data['scores']) == 14
    assert len(data['pairs']) == 21
    assert len({frozenset((pair['a']['seat'], pair['b']['seat']))
                for pair in data['pairs']}) == 21
    assert all(pair['a']['seat'] != pair['b']['seat'] for pair in data['pairs'])
