"""Pin the -n rule of scripts/pytest_workers.py (ticket 1215)."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest_workers as pw  # noqa: E402

SCRIPT = Path(pw.__file__)


def test_workers_follow_cpus_between_floor_and_cap():
    assert pw.workers(1, None, True) == pw.FLOOR
    assert pw.workers(pw.FLOOR + 1, None, True) == pw.FLOOR + 1
    assert pw.workers(10_000, None, True) == pw.CAP


def test_floor_and_cap_are_ordered():
    assert 1 <= pw.FLOOR <= pw.CAP


def test_override_wins_unclamped_and_zero_is_serial():
    assert pw.workers(4, "3", True) == 3
    assert pw.workers(4, str(pw.CAP * 4), True) == pw.CAP * 4
    assert pw.workers(4, "0", True) == 0


def test_garbage_override_falls_back_to_the_rule():
    assert pw.workers(4, "many", True) == pw.workers(4, None, True)
    assert pw.workers(4, "", True) == pw.workers(4, None, True)


def test_serial_without_xdist_even_with_override():
    assert pw.workers(32, None, False) == 0
    assert pw.workers(32, "8", False) == 0


def test_usable_cpus_is_positive_and_honours_affinity():
    import os

    n = pw.usable_cpus()
    assert 1 <= n <= (os.cpu_count() or n)
    if hasattr(os, "sched_getaffinity"):
        assert n == len(os.sched_getaffinity(0))


@pytest.mark.integration
def test_cli_prints_flag_or_nothing():
    env = {"PATH": "/usr/bin:/bin", "IDH_TEST_WORKERS": "0"}
    out = subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True, check=True)
    assert out.stdout == ""
    env["IDH_TEST_WORKERS"] = "5"
    out = subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True, check=True)
    # "-n 5" when xdist is importable here, "" when it is not: never anything else.
    assert out.stdout in ("-n 5\n", "")
