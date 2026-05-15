"""
Tests for /dream skill helper scripts.
Scripts are pure I/O — no LLM calls, no Anthropic dependency.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

DREAM_DIR = Path(__file__).parent.parent / "skills" / "dream"
READ_INDEX = DREAM_DIR / "read-index.py"
COMMIT_PY = DREAM_DIR / "commit.py"


@pytest.fixture
def fixture_memory_dir(tmp_path):
    projects_dir = tmp_path / ".claude" / "projects" / "test-project" / "memory"
    projects_dir.mkdir(parents=True)

    (projects_dir / "feedback_vim.md").write_text(
        "---\nname: feedback_vim\ndescription: vim preference\nmetadata:\n  type: feedback\n---\nUser prefers vim.\n"
    )
    (projects_dir / "feedback_emacs.md").write_text(
        "---\nname: feedback_emacs\ndescription: emacs preference\nmetadata:\n  type: feedback\n---\nUser switched to emacs.\n"
    )
    (projects_dir / "MEMORY.md").write_text(
        "## Entries\n\n"
        "- [feedback_vim](feedback_vim.md) — Editor preference: vim\n"
        "- [feedback_emacs](feedback_emacs.md) — Editor preference: emacs\n"
    )
    return tmp_path


def _run(script, *args, home):
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


def test_read_index_returns_entries(fixture_memory_dir):
    result = _run(READ_INDEX, "test-project", home=fixture_memory_dir)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["project"] == "test-project"
    assert len(data["entries"]) == 2
    filenames = {e["filename"] for e in data["entries"]}
    assert filenames == {"feedback_vim.md", "feedback_emacs.md"}
    for entry in data["entries"]:
        assert entry["content"]


def test_read_index_missing_project(tmp_path):
    result = _run(READ_INDEX, "nonexistent", home=tmp_path)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert "error" in data


def test_read_index_empty_index(tmp_path):
    mem = tmp_path / ".claude" / "projects" / "empty" / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("# Memory index\n\n## Key insights\n\n")

    result = _run(READ_INDEX, "empty", home=tmp_path)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["entries"] == []


def test_skill_md_instructs_preserve_evolution():
    content = (DREAM_DIR / "SKILL.md").read_text()
    assert "evolution" in content.lower() or "preserve" in content.lower()


def test_commit_py_has_rollback_subcommand():
    assert "rollback" in COMMIT_PY.read_text()


def test_no_anthropic_import_in_scripts():
    for script in [READ_INDEX, COMMIT_PY]:
        source = script.read_text()
        assert "import anthropic" not in source, f"{script.name} imports anthropic"
        assert "from anthropic" not in source, f"{script.name} imports anthropic"
