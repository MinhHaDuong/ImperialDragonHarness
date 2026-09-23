"""A review must identify the PR checkout even when launched from another cwd."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review-pr-anchor.py"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def checkout(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    (repo / "file.txt").write_text("base\n")
    git(repo, "add", "file.txt")
    git(repo, "commit", "-m", "base")
    git(repo, "branch", "feature")
    git(repo, "update-ref", "refs/remotes/origin/main", git(repo, "rev-parse", "HEAD"))
    wrong = tmp_path / "wrong"
    right = tmp_path / "right"
    git(repo, "worktree", "add", "--detach", str(wrong), "main")
    git(repo, "worktree", "add", str(right), "feature")
    (right / "file.txt").write_text("changed\n")
    git(right, "add", "file.txt")
    git(right, "commit", "-m", "change")
    return wrong, right


def invoke(tmp_path, checkout, tree):
    wrong, right = checkout
    shim = tmp_path / "gh"
    shim.write_text(
        "#!/bin/sh\n"
        'test "$PWD" = "$MOCK_GH_CWD" || exit 91\n'
        'printf \'%s\\n\' "$MOCK_PR_JSON"\n'
    )
    shim.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}",
               MOCK_GH_CWD=str(tree), MOCK_PR_JSON=json.dumps({
        "headRefOid": git(right, "rev-parse", "HEAD"), "baseRefName": "main",
    }))
    return subprocess.run([sys.executable, str(SCRIPT), "42", "--worktree", str(tree)],
                          cwd=wrong, env=env, capture_output=True, text=True)


def test_mismatched_cwd_still_reads_pr_worktree(tmp_path, checkout):
    result = invoke(tmp_path, checkout, checkout[1])
    assert result.returncode == 0, result.stderr
    assert "file.txt" in result.stdout
    assert "REVIEW-ANCHOR:" in result.stdout


def test_wrong_worktree_fails_loudly(tmp_path, checkout):
    result = invoke(tmp_path, checkout, checkout[0])
    assert result.returncode != 0
    assert "REVIEW-ANCHOR: wrong HEAD" in result.stderr


def test_empty_pr_diff_fails_loudly(tmp_path, checkout):
    wrong, right = checkout
    git(right, "reset", "--hard", "origin/main")
    result = invoke(tmp_path, checkout, right)
    assert result.returncode != 0
    assert "REVIEW-ANCHOR: empty diff" in result.stderr
