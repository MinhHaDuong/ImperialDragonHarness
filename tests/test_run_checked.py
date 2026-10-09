"""run_checked surfaces stderr and stdout on failure (positive control)."""

import pytest

from run_checked import run_checked


def test_success_returns_completed_process():
    assert run_checked(["echo", "hi"]).stdout.strip() == "hi"


def test_failure_message_carries_stderr_and_stdout():
    with pytest.raises(RuntimeError) as exc:
        run_checked(["bash", "-c", "echo OUT; echo ERR >&2; exit 3"])
    msg = str(exc.value)
    assert "exit 3" in msg and "ERR" in msg and "OUT" in msg
