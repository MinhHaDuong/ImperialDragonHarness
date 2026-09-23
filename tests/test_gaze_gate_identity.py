"""Regression contracts for gaze's isolation and gate identity (ticket 0852)."""

from pathlib import Path
import importlib.util
import os
import subprocess

import pytest


ROOT = Path(__file__).resolve().parent.parent
GAZE = ROOT / "skills/gaze/SKILL.md"
VERIFY = ROOT / "skills/verify-gate/SKILL.md"
LOCK_SCRIPT = ROOT / "scripts/gaze-gate-lock.py"

spec = importlib.util.spec_from_file_location("gaze_gate_lock", LOCK_SCRIPT)
lock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lock)


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


def test_gate_claim_is_atomic_per_pr_and_release_requires_owner(tmp_path):
    first = lock.acquire(tmp_path, "85", "/review-85")
    with pytest.raises(RuntimeError, match=f"session={first}"):
        lock.acquire(tmp_path, "85", "/other-85")
    other = lock.acquire(tmp_path, "86", "/review-86")
    with pytest.raises(RuntimeError, match="another gate"):
        lock.release(tmp_path, "85", other)
    lock.release(tmp_path, "85", first)
    lock.release(tmp_path, "86", other)
    replacement = lock.acquire(tmp_path, "85", "/new-review-85")
    lock.release(tmp_path, "85", replacement)


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
    assert not (tmp_path / ".claude/worktrees/.gaze-gates/pr-85.lock").exists()
