"""Run the cold replay contract fixture in the project's normal test gates."""

import subprocess
from pathlib import Path


def test_cold_replay_fixture():
    script = Path(__file__).with_suffix(".sh")
    subprocess.run(["bash", str(script)], check=True, timeout=30)
