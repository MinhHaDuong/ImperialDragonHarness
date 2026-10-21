"""A review seat ends within its cap, and every manifest seat reports a wall time or a failure (ticket 1099)."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'seat_clock.py'


def run(*args, timeout=30):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=timeout)


def test_timed_out_reader_is_killed_and_the_caller_continues(tmp_path):
    out = tmp_path / 'xfam.md'
    started = time.monotonic()
    # A stub caller: the capped reader hangs, the caller goes on and says so.
    caller = subprocess.run(
        ['bash', '-c', f'"{sys.executable}" "{SCRIPT}" run --cap 1 --out "{out}" -- sleep 60; '
                       'echo "exit=$?"; echo "caller continued"'],
        capture_output=True, text=True, timeout=30)
    assert time.monotonic() - started < 15
    assert 'xfam: no report (timed out after 1s)' in caller.stdout
    assert 'exit=1' in caller.stdout
    assert 'caller continued' in caller.stdout
    assert not out.exists()
    assert (tmp_path / 'xfam.md.status').read_text().strip() == 'xfam: no report (timed out after 1s)'


def test_completed_reader_lands_its_report_with_its_wall_time(tmp_path):
    out = tmp_path / 'xfam.md'
    result = run('run', '--cap', '20', '--out', str(out), '--', 'echo', 'verdict: clear')
    assert result.returncode == 0
    assert out.read_text() == 'verdict: clear\n'
    assert result.stdout.startswith('xfam: reported in ')
    assert result.stdout.strip().endswith('s')


def test_failed_start_and_failed_exit_are_named(tmp_path):
    missing = run('run', '--cap', '5', '--out', str(tmp_path / 'a.md'), '--', 'no-such-reader-cli-1099')
    assert missing.returncode == 1
    assert missing.stdout.strip() == 'a: no report (failed to start)'
    failed = run('run', '--cap', '5', '--out', str(tmp_path / 'b.md'), '--', 'bash', '-c', 'echo partial; exit 3')
    assert failed.returncode == 1
    assert failed.stdout.startswith('b: no report (failed, exit 3, ')
    assert not (tmp_path / 'b.md').exists()


def test_roster_names_every_manifest_seat(tmp_path):
    manifest = tmp_path / 'manifest.txt'
    manifest.write_text('correctness\tm\tf\tr\nscope\tm\tf\tr\nred-team\tm\tf\tr\n')
    launched = manifest.stat().st_mtime
    (tmp_path / 'correctness.md').write_text('verdict: clear\n')
    os.utime(tmp_path / 'correctness.md', (launched + 95, launched + 95))
    (tmp_path / 'red-team.md.status').write_text('red-team: no report (timed out after 600s)\n')
    (tmp_path / 'xfam.md.status').write_text('xfam: reported in 300s\n')
    result = run('roster', str(tmp_path))
    assert result.returncode == 1  # a planned seat has no report
    assert result.stdout.splitlines() == [
        'correctness: reported in 95s',
        'scope: no report',
        'red-team: no report (timed out after 600s)',
        'xfam: reported in 300s',
    ]
