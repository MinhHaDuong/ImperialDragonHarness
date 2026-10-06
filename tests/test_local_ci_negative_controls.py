"""Negative controls for the local CI runner (ticket 1041).

Each guard of the CI workflow must fail when a violation is injected. The run
takes several minutes and needs act, podman and a network, so it is opt-in:
set RUN_LOCAL_CI_NEGATIVE=1. It is skipped on the forge's runners, where act
is absent, and inside the local runner's own containers for the same reason.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "local-ci-negative-controls.sh"

pytestmark = [pytest.mark.slow, pytest.mark.integration]


@pytest.mark.skipif(
    os.environ.get("RUN_LOCAL_CI_NEGATIVE") != "1",
    reason="opt-in: set RUN_LOCAL_CI_NEGATIVE=1 (several minutes, needs act + podman)",
)
@pytest.mark.skipif(
    not (shutil.which("act") and shutil.which("podman")),
    reason="act and podman are required",
)
def test_every_guard_catches_its_violation():
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=1800,
        cwd=ROOT,
        env=child_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    caught = [line for line in result.stdout.splitlines() if ": caught - " in line]
    assert len(caught) == 9, result.stdout
