import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('analysis', Path(__file__).parents[1] / 'scripts/tournament-analysis.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def record(tmp_path, verdict, cost=0):
    (tmp_path / 'run.json').write_text(json.dumps({'verdict': verdict, 'seconds': 7200, 'cost_usd': cost}))
    return tmp_path


def test_timeout_counts_zero_and_consumed_resources(tmp_path):
    row = analysis.read_leg(record(tmp_path, 'DNF', .34), 'k')
    assert row == {'state': 'failure', 'quality': 0, 'seconds': 7200, 'cost_usd': .34}
    local = analysis.read_leg(tmp_path, 'a')
    assert local['cost_usd'] == 7200 * analysis.ELEC_USD_S


def test_provider_error_is_not_model_failure(tmp_path):
    record(tmp_path, 'VOID-EMPTY')
    session = tmp_path / 'attempts/1/sessions'
    session.mkdir(parents=True)
    (session / 'test.jsonl').write_text(json.dumps({'message': {'stopReason': 'error', 'errorMessage': '403 monthly limit'}}))
    assert analysis.read_leg(tmp_path, 'j') == {'state': 'infrastructure'}


def test_unfinished_panel_is_pending_and_zero_cost_is_valid(tmp_path):
    record(tmp_path, 'OK')
    judges = tmp_path / 'judges'
    judges.mkdir()
    for i in range(2):
        (judges / f'{i}.json').write_text(json.dumps({'parsed': {'score': 10}}))
    assert analysis.read_leg(tmp_path, 'l')['state'] == 'pending'
    (judges / '2.json').write_text(json.dumps({'parsed': {'score': 9}}))
    row = analysis.read_leg(tmp_path, 'l')
    assert row['quality'] == 29 and row['cost_usd'] == 0


def test_paired_timeout_remains_in_sample(tmp_path):
    (tmp_path / 'runs.json').write_text(json.dumps({'matrix': [{'ticket': '0001', 'arm_order': ['a', 'l', 'h']}]}))
    for arm in ['a', 'l']:
        folder = tmp_path / 'runs' / f'0001-{arm}'
        folder.mkdir(parents=True)
        record(folder, 'DNF')
    report = analysis.analyze(tmp_path)
    assert set(report['arms']) == {'a', 'l'}
    assert report['pairs']['a/l']['n'] == 1
    assert report['arms']['a']['quality_median'] == 0
