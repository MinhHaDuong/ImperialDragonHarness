"""SessionStart no longer injects the harness memory index.

Claude Code loads the repository's AGENTS.md, which tells the session to read
memory/MEMORY.md at task start, so the hook printing the index too served it
twice. This pins the removal: the index text stays out of the context printer's
output in the harness repository, a worktree of it, and elsewhere.
"""

import subprocess
from pathlib import Path

import pytest

from child_env import child_env

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "on-start-context.sh"
SENTINEL = "Search the journal for older or unprocessed experiences."


def hook_stdout(project_dir):
    env = child_env()
    if project_dir is None:
        env.pop("CLAUDE_PROJECT_DIR", None)
    else:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    result = subprocess.run(
        ["bash", str(SCRIPT)], cwd=REPO, env=env, capture_output=True, text=True,
    )
    return result.stdout


def test_index_exists_for_the_check_to_mean_something():
    assert SENTINEL in (REPO / "memory" / "MEMORY.md").read_text()


@pytest.mark.parametrize("project", ["repo", "none"])
def test_index_not_injected(project):
    assert SENTINEL not in hook_stdout(REPO if project == "repo" else None)
