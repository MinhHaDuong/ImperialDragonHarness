"""A step prints a measured `duration:` line from a clock, never an estimate (ticket 1224)."""

import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'step_clock.py'
LINE = re.compile(r'^duration: (\d+h\d{2}m\d{2}s|\d+m\d{2}s|\d+s)$')


def run(*args, stdin=''):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True, timeout=30)


def test_stubbed_step_duration_is_well_formed_and_at_least_the_sleep():
    t0 = run('start').stdout.strip()
    time.sleep(2)
    line = run('end', t0).stdout.strip()
    assert LINE.match(line), line
    assert int(line.split()[1].rstrip('s')) >= 2


def test_formats_minutes_and_hours():
    sys.path.insert(0, str(SCRIPT.parent))
    import step_clock
    assert step_clock.duration_line('1000', now=1252) == 'duration: 4m12s'
    assert step_clock.duration_line('100', now=3825) == 'duration: 1h02m05s'


@pytest.mark.parametrize('token', ['', 'garbage', '9999999999'])
def test_unreadable_clock_is_not_measured_never_guessed(token):
    assert run('end', token).stdout.strip() == 'duration: not measured'
    assert run('end').stdout.strip() == 'duration: not measured'


def test_table_names_total_and_slowest_step():
    out = run('table', stdin='7 gaze 100 160\n7 gate-r1 160 400\n7 merge 410 430\n').stdout
    assert 'total            5m30s' in out
    assert 'slowest: gate-r1 (4m00s)' in out


@pytest.mark.parametrize('token', ['-5', '0'])
def test_non_positive_start_is_not_measured(token):
    assert run('end', token).stdout.strip() == 'duration: not measured'


def test_table_lists_unreadable_rows_and_never_negative():
    out = run('table', stdin='7 gaze not-measured\n7 gate 1 5\n8 merge 10 5\n').stdout
    assert out.count('not measured') == 2
    assert ' -' not in out


def test_seconds_mode():
    assert run('end', '--seconds', '-5').stdout.strip() == 'na'
    t0 = run('start').stdout.strip()
    assert run('end', '--seconds', t0).stdout.strip().isdigit()
