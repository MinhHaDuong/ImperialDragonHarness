"""wait-roster.py blocks on a seat roster within a deadline and a per-call slice (ticket 1327)."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'wait-roster.py'


def wait(*args, timeout=30):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=timeout)


def until(seconds):
    return str(time.time() + seconds)


def test_all_present_exits_zero(tmp_path):
    (tmp_path / 'a.md').write_text('x')
    (tmp_path / 'b.md').write_text('x')
    assert wait(str(tmp_path), 'a', 'b', '--until', until(30)).returncode == 0


def test_deadline_lists_the_missing_name(tmp_path):
    (tmp_path / 'a.md').write_text('x')
    done = wait(str(tmp_path), 'a', 'b', '--until', until(1))
    assert done.returncode == 1
    assert done.stdout.split() == ['b']


def test_part_file_does_not_count(tmp_path):
    (tmp_path / 'a.md.part').write_text('half')
    done = wait(str(tmp_path), 'a', '--until', until(1))
    assert (done.returncode, done.stdout.split()) == (1, ['a'])


def test_deadline_already_past_returns_at_once(tmp_path):
    started = time.monotonic()
    done = wait(str(tmp_path), 'a', '--until', until(-5))
    assert (done.returncode, done.stdout.split()) == (1, ['a'])
    assert time.monotonic() - started < 5


def test_slice_ends_before_the_deadline_with_exit_three(tmp_path):
    done = wait(str(tmp_path), 'a', '--until', until(60), '--slice', '1')
    assert done.returncode == 3
    assert 're-issue' in done.stderr


def test_report_landing_during_the_wait_is_seen(tmp_path):
    late = subprocess.Popen(['bash', '-c', f'sleep 1; touch "{tmp_path}/a.md.part"; mv "{tmp_path}/a.md.part" "{tmp_path}/a.md"'])
    try:
        assert wait(str(tmp_path), 'a', '--until', until(20)).returncode == 0
    finally:
        late.wait()


def test_manifest_roster_ignores_a_past_rounds_report(tmp_path):
    stale = tmp_path / 'a.md'
    stale.write_text('old')
    os.utime(stale, (time.time() - 100, time.time() - 100))
    (tmp_path / 'manifest.txt').write_text('# budget: 5m\na\tmodel\tfam\treason\nb\tmodel\tfam\treason\n')
    (tmp_path / 'b.md').write_text('new')
    done = wait(str(tmp_path), '--roster', str(tmp_path / 'manifest.txt'), '--until', until(1))
    assert (done.returncode, done.stdout.split()) == (1, ['a'])


def test_plain_roster_file_and_newer_than(tmp_path):
    (tmp_path / 'roster.txt').write_text('a\nb\n')
    (tmp_path / 'a.md').write_text('x')
    (tmp_path / 'b.md').write_text('x')
    assert wait(str(tmp_path), '--roster', str(tmp_path / 'roster.txt'), '--until', until(5)).returncode == 0
    future = tmp_path / 'mark'
    future.write_text('')
    os.utime(future, (time.time() + 50, time.time() + 50))
    done = wait(str(tmp_path), 'a', '--until', until(1), '--newer-than', str(future))
    assert done.returncode == 1


def test_usage_errors_exit_two(tmp_path):
    assert wait(str(tmp_path), '--until', until(1)).returncode == 2
    assert wait(str(tmp_path), 'a').returncode == 2
    assert wait(str(tmp_path / 'nope'), 'a', '--until', until(1)).returncode == 2
