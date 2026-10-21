"""scripts/check-pipefail.sh, the gate's pipefail-guard (ticket 1156)."""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-pipefail.sh"


def run(*paths):
    return subprocess.run(["bash", str(SCRIPT), *map(str, paths)], capture_output=True, text=True, env=child_env())


def test_catches_a_script_without_pipefail(tmp_path):
    bad = tmp_path / "bad.sh"
    bad.write_text("#!/bin/bash\necho hi\n", encoding="utf-8")
    assert run(bad).returncode == 1


def test_passes_a_compliant_script(tmp_path):
    good = tmp_path / "good.sh"
    good.write_text("#!/bin/bash\nset -euo pipefail\necho hi\n", encoding="utf-8")
    assert run(good).returncode == 0


def test_unreadable_path_is_not_an_all_clear(tmp_path):
    result = run(tmp_path / "absent.sh")
    assert result.returncode != 0
    assert "OK" not in result.stdout
