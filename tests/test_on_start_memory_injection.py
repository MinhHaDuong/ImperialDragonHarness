"""SessionStart injects the harness memory index only for this repository.

Ticket 0920 scoped the legacy cross-project injection: memory/MEMORY.md is
cat-ed only when the session's project shares this repository's git common
dir — the primary checkout or one of its worktrees. Nothing covered that
gate when it landed, so a regression back to the unconditional cat passed
the whole suite; this module is that regression test.
"""

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "on-start.sh"
SENTINEL = "Search the journal for older or unprocessed experiences."


def hook_stdout(project_dir):
    env = os.environ.copy()
    if project_dir is None:
        env.pop("CLAUDE_PROJECT_DIR", None)
    else:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_index_injected_for_this_repository():
    assert SENTINEL in hook_stdout(REPO)


def test_index_injected_for_a_worktree_of_this_repository(tmp_path):
    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    try:
        assert SENTINEL in hook_stdout(worktree)
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO,
            check=True,
            capture_output=True,
        )


def test_index_not_injected_for_an_unrelated_git_repo(tmp_path):
    repo = tmp_path / "unrelated"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    assert SENTINEL not in hook_stdout(repo)


def test_index_not_injected_for_a_non_git_dir(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert SENTINEL not in hook_stdout(plain)


def test_index_not_injected_without_project_dir():
    assert SENTINEL not in hook_stdout(None)
