"""Ticket 1384: every headless launcher writes one launch line per child.

Seats are `sh` stubs; the archive root is the autouse temporary one (tests/conftest.py), never the host's.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import launch_line  # noqa: E402

CLOCK = SCRIPTS / 'seat_clock.py'
KEYS = {'ts_start', 'ts_end', 'host', 'parent_runtime', 'parent_session', 'child_runtime', 'child_session',
        'seat', 'cwd', 'unit', 'exit', 'out'}
SCRUB = ('CLAUDECODE', 'CLAUDE_CODE_SESSION_ID', 'CODEX_THREAD_ID', 'PI_CODING_AGENT', 'AI_AGENT',
         'IDH_PI_SESSION_ID', 'IDH_UNIT')


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in SCRUB}
    return {**env, **extra}


def seat(tmp_path, *command, env=None, name='s'):
    return subprocess.run([sys.executable, str(CLOCK), 'run', '--cap', '20', '--out', str(tmp_path / f'{name}.md'),
                           '--', *command], capture_output=True, text=True, timeout=60, env=env or clean_env())


def lines():
    return [json.loads(line) for line in launch_line.launches_path().read_text().splitlines()]


@pytest.mark.integration
def test_stub_seat_appends_one_well_formed_line_per_run(tmp_path):
    env = clean_env(CLAUDECODE='1', CLAUDE_CODE_SESSION_ID='parent-1', IDH_UNIT='t1384')
    for _ in range(2):
        result = seat(tmp_path, 'sh', '-c', 'echo hi; exit 3', env=env)
        assert result.returncode == 1 and result.stdout.startswith('s: no report (failed, exit 3')
    first, second = lines()
    assert set(first) == KEYS
    assert (first['parent_runtime'], first['parent_session'], first['exit'], first['seat']) == \
        ('claude', 'parent-1', 3, 's')
    assert first['child_runtime'] == 'sh' and first['child_session'] == 'not captured' and first['unit'] == 't1384'
    assert first['out'].endswith('/s.md')  # ticket 1399: the report path names the review's panel
    assert first['ts_start'] <= first['ts_end'] and second['parent_session'] == 'parent-1'


@pytest.mark.integration
def test_unwritable_launches_file_changes_neither_status_nor_exit_code(tmp_path):
    ok = seat(tmp_path, 'echo', 'verdict: clear', name='a')
    root = tmp_path / 'blocked'
    root.write_text('a file where the archive root should be')
    broken = seat(tmp_path, 'echo', 'verdict: clear', name='b', env=clean_env(IDH_ARCHIVE_ROOT=str(root)))
    assert (broken.returncode, broken.stdout.replace('b:', 'a:')) == (ok.returncode, ok.stdout)
    assert broken.stderr.count('launch_line:') == 1 and ok.stderr == ''


@pytest.mark.integration
def test_pinned_claude_id_and_codex_log_id_are_read_not_guessed(tmp_path):
    seat(tmp_path, 'sh', '-c', 'exit 0', '--session-id', 'c-uuid-1')
    codex = tmp_path / 'codex'
    codex.write_text('#!/bin/sh\necho "session id: 0190abcd-1234" >&2\n')
    codex.chmod(0o755)
    seat(tmp_path, str(codex), name='cx')
    seat(tmp_path, 'sh', '-c', 'echo quiet >&2', name='none')
    assert [row['child_session'] for row in lines()] == ['c-uuid-1', '0190abcd-1234', 'not captured']


def test_parent_pi_carries_its_session_id_or_not_exported():
    assert launch_line.parent({'PI_CODING_AGENT': 'true', 'IDH_PI_SESSION_ID': 'pi-9'}) == ('pi', 'pi-9')
    assert launch_line.parent({'PI_CODING_AGENT': 'true'}) == ('pi', 'not exported')
    assert launch_line.parent({}) == ('unknown', 'not exported')


def test_record_writes_a_pi_parent_line(monkeypatch):
    assert launch_line.record(seat='x', child_runtime='pi', child_session='f', ts_start=0, ts_end=1, exit=0,
                              cwd='/w', env={'PI_CODING_AGENT': 'true', 'IDH_PI_SESSION_ID': 'pi-9'})
    assert [(row['parent_runtime'], row['parent_session']) for row in lines()] == [('pi', 'pi-9')]


def test_pin_only_adds_the_session_id():
    argv, sid = launch_line.pin(['claude', '-p', '--model', 'm', 'P'])
    assert argv[:3] == ['claude', '--session-id', sid] and argv[3:] == ['-p', '--model', 'm', 'P']
    assert launch_line.pin(['codex', 'exec']) == (['codex', 'exec'], None)
    assert launch_line.pin(['pi', '--session-id', 'mine'])[1] is None


def test_child_from_names_the_spool_files(tmp_path):
    (tmp_path / '2026_pi-id-1.jsonl').write_text('{}')
    assert launch_line.child_from(['pi', '--session-id', 'pi-id-1'], None, tmp_path)[1] == str(tmp_path / '2026_pi-id-1.jsonl')
    assert launch_line.child_from(['pi', '--session-id', 'gone'], None, tmp_path)[1] == 'not captured'
    assert launch_line.child_from(['aider'], None, tmp_path)[1] == str(tmp_path / 'chat.md')
    assert launch_line.child_from(['vibe'], None, tmp_path)[1] == str(tmp_path)


def test_unit_falls_back_to_the_git_branch_then_a_dash(tmp_path):
    assert launch_line.unit({'IDH_UNIT': 'u'}) == 'u'
    assert launch_line.unit({}, cwd=tmp_path) == '-'
