"""Shared git helpers for harness scripts."""

import subprocess
import sys
from pathlib import Path


def _default_branch(project: Path) -> str:
    """Return the remote default branch name, falling back to 'main'."""
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=False,
            cwd=project,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(
            f"WARNING: git symbolic-ref timed out for {project}, falling back to 'main'",
            file=sys.stderr,
        )
        return "main"
    return (
        result.stdout.strip().removeprefix("origin/")
        if result.returncode == 0
        else "main"
    )
