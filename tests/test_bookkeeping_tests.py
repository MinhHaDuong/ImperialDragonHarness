"""scripts/bookkeeping-tests.sh: the bookkeeping tier's test check (ticket 1221).

A bookkeeping-only merge (tickets, STATE.md, memory) must not turn main red,
so its record runs every test that reads the repository's own bookkeeping
data, selected at run time so a new such test is never left out.
"""

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bookkeeping-tests.sh"


def run(cwd):
    env = {**os.environ, "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV", "fixture")}
    return subprocess.run(["bash", str(SCRIPT)], cwd=cwd, capture_output=True, text=True, env=env)


def write(root, name, body):
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests" / name).write_text(body, encoding="utf-8")


def test_runs_live_readers_only_and_fails_on_their_failure(tmp_path):
    write(tmp_path, "test_live.py", 'REPO = None\n\ndef test_cap():\n    assert "x" == "y"  # REPO / "STATE.md"\n')
    write(tmp_path, "test_other.py", "def test_other():\n    assert False\n")
    result = run(tmp_path)
    assert result.returncode != 0
    assert "test_live.py" in result.stdout and "test_other.py" not in result.stdout


def test_passes_when_live_readers_pass(tmp_path):
    write(tmp_path, "test_live.py", 'def test_mem():\n    assert True  # ROOT / "memory"\n')
    write(tmp_path, "test_other.py", "def test_other():\n    assert False\n")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_live_reader_found_is_an_error(tmp_path):
    write(tmp_path, "test_other.py", "def test_other():\n    assert True\n")
    assert run(tmp_path).returncode != 0
