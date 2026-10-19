"""Portable SQL reference and conservative external-input invalidation."""
import importlib.util
from pathlib import Path
import sqlite3
import subprocess

import pytest

from child_env import child_env

spec = importlib.util.spec_from_file_location(
    'smart_testing', Path(__file__).resolve().parents[1] / 'scripts/smart_testing.py')
smart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smart)


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


@pytest.mark.integration
def test_external_inputs_include_untracked_and_deleted_data(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True, env=child_env())
    data = tmp_path / 'fixture.txt'
    data.write_text('a')
    subprocess.run(['git', 'add', 'fixture.txt'], cwd=tmp_path, check=True, env=child_env())
    first = smart.external_inputs(tmp_path)
    data.write_text('b')
    assert smart.external_inputs(tmp_path) != first
    data.unlink()
    assert smart.external_inputs(tmp_path) != first
