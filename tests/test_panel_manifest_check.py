"""The panel manifest rejects a seat whose model, family or reason is missing."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'panel-manifest-check.py'
spec = importlib.util.spec_from_file_location('panel_manifest_check', SCRIPT)
check_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_mod)

GOOD = 'correctness\tmid-model\tfamily-a\tlogic needs reasoning\nscope\tsmall-model\tfamily-b\tmechanical diff check\n'


def test_complete_manifest_passes():
    assert check_mod.check(GOOD) == []


def test_empty_model_rejected():
    assert check_mod.check('scope\t\tfamily-b\tmechanical\n')


def test_empty_reason_rejected():
    assert check_mod.check('scope\tsmall-model\tfamily-b\t\n')


def test_old_one_column_manifest_rejected():
    assert check_mod.check('scope\ncorrectness\n')


def test_empty_manifest_rejected():
    assert check_mod.check('\n# comment only\n')


def test_main_exit_codes(tmp_path, capsys):
    good, bad = tmp_path / 'good.txt', tmp_path / 'bad.txt'
    good.write_text(GOOD)
    bad.write_text('scope\t\tfamily-b\tmechanical\n')
    assert check_mod.main(['x', str(good)]) == 0
    assert check_mod.main(['x', str(bad)]) == 1
    assert 'PANEL-MANIFEST:' in capsys.readouterr().err
