"""Portable SQL reference and conservative external-input invalidation."""
import json
import re
import shutil
import sys
from pathlib import Path
import sqlite3
import subprocess

import pytest

from child_env import child_env

from scripts import smart_testing as smart


def test_restore_relocates_memory(tmp_path):
    original = tmp_path / 'original.db'
    with sqlite3.connect(original) as connection:
        connection.execute('PRAGMA user_version=14')
        connection.execute('CREATE TABLE memory (value TEXT)')
        connection.execute("INSERT INTO memory VALUES ('known-positive')")
        dump = tmp_path / 'reference.sql'
        dump.write_text('PRAGMA user_version=14;\n' + '\n'.join(connection.iterdump()))
    relocated = tmp_path / 'other-worktree' / 'memory.db'
    smart.restore(dump, relocated)
    with sqlite3.connect(relocated) as connection:
        assert connection.execute('PRAGMA user_version').fetchone() == (14,)
        assert connection.execute('SELECT value FROM memory').fetchone() == ('known-positive',)


def test_bad_dump_does_not_publish_database(tmp_path):
    dump = tmp_path / 'bad.sql'
    dump.write_text('invalid SQL')
    database = tmp_path / 'private.db'
    with pytest.raises(sqlite3.Error):
        smart.restore(dump, database)
    assert not database.exists()


@pytest.fixture
def smart_repository(tmp_path):
    """A real tiny project: exercise native Testmon without the harness suite."""
    pytest.importorskip('testmon')
    root = tmp_path / 'project'
    (root / 'scripts').mkdir(parents=True)
    (root / 'tests').mkdir()
    source = Path(__file__).resolve().parents[1] / 'scripts'
    for script in source.glob('smart_testing*.py'):
        shutil.copy2(script, root / 'scripts' / script.name)
    (root / '.gitignore').write_text(
        '.smart-testing/\n.pytest_cache/\n__pycache__/\n')
    (root / 'pytest.ini').write_text(
        '[pytest]\nmarkers =\n'
        '    integration: subprocess tests\n'
        '    slow: slow tests\n'
        '    adherence: mechanical checks\n')
    (root / 'fixture.txt').write_text('1')
    (root / 'helper.py').write_text(
        'from pathlib import Path\n'
        'def value():\n'
        '    return int(Path("fixture.txt").read_text())\n')
    (root / 'tests/test_case.py').write_text(
        'from pathlib import Path\n'
        'import os\n'
        'from helper import value\n'
        'def test_value():\n'
        '    assert value() == 1\n'
        '    assert not Path("fixture.txt").stat().st_mode & 0o111\n')
    subprocess.run(['git', 'init', '-q', str(root)], check=True, env=child_env())
    subprocess.run(['git', 'add', '.'], cwd=root, check=True, env=child_env())
    subprocess.run(
        ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
         'commit', '-qm', 'fixture'], cwd=root, check=True, env=child_env())
    return root


def _smart_run(root, *arguments, bytecode=False):
    env = child_env()
    for key in ('TESTMON_DATAFILE', 'PYTEST_ADDOPTS', 'PYTEST_PLUGINS'):
        env.pop(key, None)
    if bytecode:
        env.pop('PYTHONDONTWRITEBYTECODE', None)
    else:
        env['PYTHONDONTWRITEBYTECODE'] = '1'
    return subprocess.run(
        [sys.executable, '-m', 'scripts.smart_testing', *arguments], cwd=root,
        env=env, text=True, capture_output=True, timeout=40)


def _assert_passed(result):
    assert result.returncode == 0, result.stdout + result.stderr
    assert re.search(r'\b1 passed\b', result.stdout), result.stdout + result.stderr


def _assert_unchanged(result):
    assert result.returncode == 0, result.stdout + result.stderr
    assert not re.search(r'\b[1-9][0-9]* passed\b', result.stdout), result.stdout


@pytest.mark.integration
def test_reference_adoption_checks_private_input_baseline(smart_repository, tmp_path):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh'))
    # A different branch learns a new fixture and matching implementation.
    branch = tmp_path / 'branch'
    shutil.copytree(root, branch, ignore=shutil.ignore_patterns('.smart-testing'))
    (branch / 'fixture.txt').write_text('2')
    helper = branch / 'helper.py'
    helper.write_text(helper.read_text().replace('.read_text())', '.read_text()) - 1'))
    _assert_passed(_smart_run(branch, '--refresh'))
    # Adopt that branch's data/reference, then locally revert its implementation.
    # The private DB still remembers the old implementation and old fixture.
    shutil.copy2(branch / 'fixture.txt', root / 'fixture.txt')
    shutil.copytree(branch / 'tests/smart-testing', root / 'tests/smart-testing',
                    dirs_exist_ok=True)
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'assert 2 == 1' in result.stdout


@pytest.mark.integration
def test_python_source_read_as_data_invalidates_consumer(smart_repository):
    root = smart_repository
    source = root / 'source.py'
    source.write_text('VALUE = 1\n')
    (root / 'tests/test_case.py').write_text(
        'from pathlib import Path\n'
        'def test_source():\n'
        '    assert "forbidden" not in Path("source.py").read_text()\n')
    _assert_passed(_smart_run(root, '--refresh'))
    source.write_text('VALUE = 1\n# forbidden\n')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_unrelated_text_change_keeps_native_selection(smart_repository):
    root = smart_repository
    (root / 'unrelated.md').write_text('An unrelated working note.\n')
    _assert_passed(_smart_run(root, '--refresh'))
    (root / 'unrelated.md').write_text('An unrelated note changed.\n')
    _assert_unchanged(_smart_run(root))


@pytest.mark.integration
def test_failed_forced_consumer_retries_until_fixed(smart_repository):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh'))
    (root / 'fixture.txt').write_text('2')
    for _ in range(2):
        result = _smart_run(root)
        assert result.returncode == 1, result.stdout + result.stderr
        assert '1 failed' in result.stdout
    (root / 'fixture.txt').write_text('1')
    assert _smart_run(root).returncode == 0


@pytest.mark.integration
@pytest.mark.parametrize('bytecode', [False, True], ids=['source', 'copied-bytecode'])
def test_relocated_reference_restores_native_and_input_state(smart_repository, tmp_path, bytecode):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh', bytecode=bytecode))
    if bytecode:
        assert list((root / 'tests/__pycache__').glob('test_case*.pyc'))
    relocated = tmp_path / 'relocated'
    shutil.copytree(root, relocated, ignore=shutil.ignore_patterns('.smart-testing'))
    _assert_unchanged(_smart_run(relocated, bytecode=bytecode))
    # Re-observe reads from relocated pytest-rewritten code, whose co_filename
    # can retain the original checkout path even though __file__ is current.
    _assert_passed(_smart_run(relocated, '--refresh', bytecode=bytecode))
    (relocated / 'fixture.txt').write_text('2')
    result = _smart_run(relocated, bytecode=bytecode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'assert 2 == 1' in result.stdout


@pytest.mark.integration
def test_mode_only_known_input_change_runs_consumer(smart_repository):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh'))
    fixture = root / 'fixture.txt'
    fixture.chmod(fixture.stat().st_mode | 0o100)
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_compatible_reference_update_preserves_private_database(smart_repository):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh'))
    database = root / '.smart-testing/testmon.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE preserved_learning (value TEXT)')
        connection.execute("INSERT INTO preserved_learning VALUES ('local')")
    metadata = root / 'tests/smart-testing/reference.json'
    reference = json.loads(metadata.read_text())
    reference['source_commit'] = 'a-different-compatible-reference'
    metadata.write_text(json.dumps(reference))
    _assert_unchanged(_smart_run(root))
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT value FROM preserved_learning').fetchone() == ('local',)


@pytest.mark.integration
@pytest.mark.parametrize('missing', ['testmon.db', 'inputs.json'])
def test_incomplete_private_pair_learns_safely(smart_repository, missing):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh'))
    (root / '.smart-testing' / missing).unlink(missing_ok=True)
    _assert_passed(_smart_run(root))
    assert (root / '.smart-testing/testmon.db').exists()
    assert (root / '.smart-testing/inputs.json').exists()


@pytest.mark.integration
def test_importlib_resources_read_invalidates_consumer(smart_repository):
    root = smart_repository
    package = root / 'fixtures'
    package.mkdir()
    (package / '__init__.py').write_text('')
    data = package / 'data.txt'
    data.write_text('yes')
    (root / 'tests/test_case.py').write_text(
        'from importlib.resources import files\n'
        'def test_resource():\n'
        '    assert files("fixtures").joinpath("data.txt").read_text() == "yes"\n')
    _assert_passed(_smart_run(root, '--refresh'))
    data.write_text('no')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_module_collection_read_only_forces_its_consumer(smart_repository, tmp_path):
    root = smart_repository
    marker = tmp_path / 'unrelated-test-ran'
    data = root / 'data.txt'
    data.write_text('yes')
    (root / 'tests/test_case.py').unlink()
    (root / 'tests/test_first.py').write_text(
        'from pathlib import Path\n'
        'DATA = Path("data.txt").read_text()\n'
        'def test_first():\n'
        '    assert DATA in ("yes", "no")\n')
    (root / 'tests/test_second.py').write_text(
        'from pathlib import Path\n'
        'def test_second():\n'
        f'    Path({str(marker)!r}).write_text("ran")\n')
    result = _smart_run(root, '--refresh')
    assert result.returncode == 0, result.stdout + result.stderr
    assert '2 passed' in result.stdout
    assert marker.exists(), 'The baseline must execute the negative-control test.'
    marker.unlink()
    data.write_text('no')
    _assert_passed(_smart_run(root))
    assert not marker.exists(), 'A collection read must not force unrelated modules.'


@pytest.mark.integration
@pytest.mark.parametrize("lazy", [False, True], ids=["collection", "runtime"])
def test_imported_module_initializer_function_invalidates_all_readers(smart_repository, lazy):
    root = smart_repository
    (root / 'tests/test_case.py').unlink()
    (root / 'fixture.txt').write_text('yes')
    (root / 'shared.py').write_text(
        'from pathlib import Path\n'
        'def load():\n'
        '    return Path("fixture.txt").read_text()\n'
        'DATA = load()\n')
    for name, assertion in (('a', 'DATA in ("yes", "no")'), ('b', 'DATA == "yes"')):
        imports = '' if lazy else 'from shared import DATA\n'
        body_import = '    from shared import DATA\n' if lazy else ''
        (root / f'tests/test_{name}.py').write_text(
            imports + f'def test_{name}():\n' + body_import + f'    assert {assertion}\n')
    baseline = _smart_run(root, '--refresh')
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    assert '2 passed' in baseline.stdout
    (root / 'fixture.txt').write_text('no')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'test_b' in result.stdout
    assert '1 failed, 1 passed' in result.stdout


@pytest.mark.integration
@pytest.mark.parametrize('tier', ['slow', 'integration', 'adherence'])
def test_all_cost_tiers_reuse_and_invalidate(smart_repository, tier):
    root = smart_repository
    test = root / 'tests/test_case.py'
    test.write_text('import pytest\n' + test.read_text().replace(
        'def test_value():', f'@pytest.mark.{tier}\ndef test_value():'))
    _assert_passed(_smart_run(root, '--refresh'))
    _assert_unchanged(_smart_run(root))
    (root / 'fixture.txt').write_text('2')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_live_opt_out_runs_even_when_cached_code_is_unchanged(smart_repository, tmp_path):
    root = smart_repository
    external = tmp_path / 'external.txt'
    external.write_text('yes')
    (root / 'tests/test_live.py').write_text(
        'from pathlib import Path\nimport pytest\n'
        '@pytest.mark.smart_always\ndef test_live():\n'
        f'    assert Path({str(external)!r}).read_text() == "yes"\n')
    assert _smart_run(root, '--refresh').returncode == 0
    _assert_passed(_smart_run(root))  # Only the live test runs again.
    external.write_text('no')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_deleted_live_module_is_removed_from_manifest(smart_repository):
    root = smart_repository
    live = root / 'tests/test_live.py'
    live.write_text('import pytest\n@pytest.mark.smart_always\ndef test_live():\n    pass\n')
    assert _smart_run(root, '--refresh').returncode == 0
    live.unlink()
    _assert_unchanged(_smart_run(root))
    state = json.loads((root / '.smart-testing/inputs.json').read_text())
    assert state['always'] == []


@pytest.mark.integration
@pytest.mark.parametrize('module_command', [False, True])
def test_child_entrypoint_changes_invalidate(smart_repository, module_command):
    root = smart_repository
    (root / 'child.py').write_text('print("yes")\n')
    arguments = "[sys.executable, '-m', 'child']" if module_command else "[sys.executable, 'child.py']"
    (root / 'tests/test_case.py').write_text(
        'import subprocess\nimport sys\nimport pytest\n'
        '@pytest.mark.integration\ndef test_child():\n'
        f'    assert subprocess.check_output({arguments}).strip() == b"yes"\n')
    _assert_passed(_smart_run(root, '--refresh'))
    _assert_unchanged(_smart_run(root))
    (root / 'child.py').write_text('print("no")\n')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_declared_child_inputs_include_new_glob_members(smart_repository):
    root = smart_repository
    (root / 'assets').mkdir()
    (root / 'assets/a.txt').write_text('yes')
    (root / 'child.py').write_text(
        'from pathlib import Path\n'
        'assert all(p.read_text() == "yes" for p in Path("assets").glob("*.txt"))\n')
    (root / 'tests/test_case.py').write_text(
        'import subprocess\nimport sys\nimport pytest\n'
        '@pytest.mark.smart_inputs("assets/*.txt")\n'
        '@pytest.mark.slow\ndef test_child():\n'
        '    subprocess.run([sys.executable, "child.py"], check=True)\n')
    _assert_passed(_smart_run(root, '--refresh'))
    _assert_unchanged(_smart_run(root))
    (root / 'assets/b.txt').write_text('no')
    result = _smart_run(root)
    assert result.returncode == 1, result.stdout + result.stderr
    assert '1 failed' in result.stdout


@pytest.mark.integration
def test_expanding_old_fast_cache_learns_new_scope(smart_repository):
    root = smart_repository
    _assert_passed(_smart_run(root, '--refresh'))
    state_path = root / '.smart-testing/inputs.json'
    state = json.loads(state_path.read_text())
    state.pop('scope')
    state_path.write_text(json.dumps(state))
    _assert_passed(_smart_run(root))
    assert json.loads(state_path.read_text())['scope'] == smart.SCOPE
    _assert_unchanged(_smart_run(root))
