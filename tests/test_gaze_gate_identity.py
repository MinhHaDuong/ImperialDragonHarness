"""Regression contracts for gaze's isolation and gate identity (ticket 0852).

The per-PR claim lock of 0852 was deleted by ticket 0976; the gate identity
fields and the no-fallback worktree setup remain."""

from pathlib import Path
import os
import subprocess

import pytest


ROOT = Path(__file__).resolve().parent.parent
GAZE = ROOT / "skills/gaze/SKILL.md"
VERIFY = ROOT / "skills/verify-gate/SKILL.md"


def test_worktree_creation_failure_stops_gaze():
    setup = GAZE.read_text().split("**Isolation setup:**", 1)[1].split(
        "## Review scratch cleanup", 1
    )[0]
    assert "git worktree add" in setup
    assert "if ! git worktree add" in setup
    assert 'test -d "$review_tree"' in setup
    assert "gaze: cannot create isolated review worktree" in setup


def test_verdict_comment_names_gate_identity():
    template = VERIFY.read_text().split("2. PR comment posted", 1)[1].split(
        "## Circuit breakers", 1
    )[0]
    for field in ("Gate session id:", "Review worktree path:", "Ruled tip SHA:"):
        assert field in template


@pytest.mark.integration
def test_denied_worktree_add_stops_without_fallback(tmp_path):
    """Run the documented setup block against a fake guard denial."""
    setup = GAZE.read_text().split("**Isolation setup:**", 1)[1].split(
        "## Review scratch cleanup", 1
    )[0]
    shell = setup.split("```bash", 1)[1].split("```", 1)[0]
    shell = shell.replace("<pr-number>", "85")
    shell = shell.replace("<resolved-branch-name>", "branch-85")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        f'case "$1 $2" in "rev-parse --show-toplevel") echo "{tmp_path}";; '
        '"fetch origin") exit 0;; "worktree add") echo "guard denied" >&2; exit 2;; '
        '*) exit 99;; esac\n'
    )
    fake_git.chmod(0o755)
    env = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}", "IDH_HOME": str(ROOT)}
    result = subprocess.run(["bash", "-c", shell], env=env, text=True, capture_output=True)
    assert result.returncode != 0
    assert "gaze: cannot create isolated review worktree" in result.stderr
    assert not (tmp_path / ".claude/worktrees/review-85").exists()
