"""SessionStart surfaces the advisory disk probe before silencing hook output."""

import os
import subprocess
from pathlib import Path

import pytest
from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.integration


def test_session_start_prints_low_disk_warning(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    python = fake_bin / "python3"
    python.write_text(
        "#!/bin/sh\n"
        "case \"$*\" in *--disk-warning*) echo 'Disk headroom warning: /tmp has 5% free (threshold: 10% free)' ;; esac\n"
    )
    python.chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    env = child_env()
    env.update({"HOME": str(home), "PATH": f"{fake_bin}:{os.environ['PATH']}"})
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/on-start.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Disk headroom warning: /tmp has 5% free" in result.stdout
