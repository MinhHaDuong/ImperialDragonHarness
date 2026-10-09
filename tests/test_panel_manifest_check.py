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


def test_duplicate_perspective_rejected():
    assert check_mod.check('a\tm\tf\tr\na\tm\tf\tr\n')
    assert check_mod.check('a\tm\tf\tr\nb\tm\tf\tr\n') == []


def test_perspective_name_charset():
    for bad in ('../x', 'a/b', 'a b', '﻿a'):
        assert check_mod.check(f'{bad}\tm\tf\tr\n'), bad
    for good in ('red-team', 'doc-propagation', 'ai_tells2'):
        assert check_mod.check(f'{good}\tm\tf\tr\n') == [], good


def test_bom_is_stripped_by_main(tmp_path):
    path = tmp_path / 'bom.txt'
    path.write_bytes(b'\xef\xbb\xbf' + GOOD.encode())
    assert check_mod.main(['x', str(path)]) == 0


def test_unreadable_manifest_fails_cleanly(tmp_path, capsys):
    binary = tmp_path / 'bin.txt'
    binary.write_bytes(b'\xff\xfe\x80\x81')
    assert check_mod.main(['x', str(tmp_path / 'missing.txt')]) == 1
    assert check_mod.main(['x', str(binary)]) == 1
    assert capsys.readouterr().err.count('PANEL-MANIFEST:') == 2


def test_main_exit_codes(tmp_path, capsys):
    good, bad = tmp_path / 'good.txt', tmp_path / 'bad.txt'
    good.write_text(GOOD)
    bad.write_text('scope\t\tfamily-b\tmechanical\n')
    assert check_mod.main(['x', str(good)]) == 0
    assert check_mod.main(['x', str(bad)]) == 1
    assert 'PANEL-MANIFEST:' in capsys.readouterr().err
