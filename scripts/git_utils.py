"""Shared git helpers for harness scripts."""

import subprocess
from pathlib import Path


def _default_branch(project: Path) -> str:
    """Return the remote default branch name, falling back to 'main'."""
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    )
    return (
        result.stdout.strip().removeprefix("origin/")
        if result.returncode == 0
        else "main"
    )
