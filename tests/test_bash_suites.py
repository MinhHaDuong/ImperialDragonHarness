"""Run every tests/*.sh suite under pytest so CI actually executes them.

Background: CI's pytest-guard runs `pytest tests/`, which only collects
`test_*.py`. The shell-based regression suites in this directory were never
wired into any runner — they passed or rotted unnoticed (e.g. the
harness-rules test referenced a path that had moved). This wrapper discovers
each `tests/*.sh` file and runs it as a subprocess, asserting exit 0, so a
broken shell suite now fails CI like any other test. New `*.sh` suites are
picked up automatically — no per-file wiring needed.

A shell suite signals failure with a non-zero exit code (the suites use
`set -euo pipefail` and `exit $fail`); its PASS/FAIL lines are surfaced on
assertion failure for debugging.
"""

import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SH_SUITES = sorted(TESTS_DIR.glob("test_*.sh"))


@pytest.mark.parametrize("script", SH_SUITES, ids=lambda p: p.name)
def test_shell_suite(script: Path):
    """Each tests/*.sh suite must exit 0."""
    result = subprocess.run(
        ["bash", str(script)],
        cwd=TESTS_DIR.parent,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
    assert result.returncode == 0, (
        f"{script.name} exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


def test_at_least_one_shell_suite_discovered():
    """Guard against a glob/layout change silently disabling all shell suites."""
    assert SH_SUITES, "no tests/*.sh suites discovered — wrapper is a no-op"
