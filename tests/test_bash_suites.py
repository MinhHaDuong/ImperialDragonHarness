"""Run every tests/*.sh suite under pytest so CI actually executes them.

Background: CI's pytest-guard runs `pytest tests/`, which only collects
`test_*.py`. The shell-based regression suites in this directory were never
wired into any runner — they passed or rotted unnoticed (e.g. the
harness-rules test referenced a path that had moved). This wrapper discovers
each `tests/*.sh` file and runs it as a subprocess, asserting exit 0 (77 = zero checks ran = skip), so a
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

from child_env import child_env

TESTS_DIR = Path(__file__).resolve().parent
SH_SUITES = sorted(TESTS_DIR.glob("test_*.sh"))


SKIP_EXIT = 77  # automake convention: the suite ran zero checks


def run_shell_suite(script: Path, cwd: Path = TESTS_DIR.parent):
    """Run one suite: exit 0 passes, 77 skips (SKIP lines as reason), else fails."""
    result = subprocess.run(
        ["bash", str(script)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=child_env(),
    )
    if result.returncode == SKIP_EXIT:
        lines = [ln for ln in result.stdout.splitlines() if ln.startswith("SKIP")]
        pytest.skip("; ".join(lines) or f"{script.name} ran zero checks")
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
    assert result.returncode == 0, (
        f"{script.name} exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


@pytest.mark.integration
@pytest.mark.parametrize("script", SH_SUITES, ids=lambda p: p.name)
def test_shell_suite(script: Path):
    """Each tests/*.sh suite must exit 0, or 77 when it ran no check (skip)."""
    run_shell_suite(script)


def test_at_least_one_shell_suite_discovered():
    """Guard against a glob/layout change silently disabling all shell suites."""
    assert SH_SUITES, "no tests/*.sh suites discovered — wrapper is a no-op"


def _run_stub(tmp_path, body):
    stub = tmp_path / "test_stub.sh"
    stub.write_text("#!/usr/bin/env bash\n" + body)
    return run_shell_suite(stub, cwd=tmp_path)


def test_stub_all_skipped_is_reported_skipped(tmp_path):
    with pytest.raises(pytest.skip.Exception) as exc:
        _run_stub(tmp_path, 'echo "SKIP: age not installed"\nexit 77\n')
    assert "age not installed" in str(exc.value)


def test_stub_passing_suite_passes(tmp_path):
    _run_stub(tmp_path, 'echo "PASS: a"\nexit 0\n')


def test_stub_failing_suite_fails(tmp_path):
    with pytest.raises(AssertionError):
        _run_stub(tmp_path, 'echo "FAIL: a"\nexit 1\n')
