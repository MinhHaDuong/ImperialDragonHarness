"""
Tests for /dream skill helper scripts.
Scripts are pure I/O — no LLM calls, no Anthropic dependency.
"""

import json
import re
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


def test_read_index_preserves_brackets_and_parenthesis_in_title(tmp_path):
    mem = tmp_path / ".claude" / "projects" / "brackets" / "memory"
    mem.mkdir(parents=True)
    title = "A test [green]] still works (for a reason)"
    filename = "feedback_brackets.md"
    (mem / filename).write_text("Bracketed lesson.\n")
    original = f"- [{title}]({filename})\n"
    (mem / "MEMORY.md").write_text("## Entries\n\n" + original)

    result = _run(READ_INDEX, "brackets", home=tmp_path)
    assert result.returncode == 0, result.stderr
    entry = json.loads(result.stdout)["entries"][0]
    assert entry["title"] == title
    assert entry["filename"] == filename
    assert f'- [{entry["title"]}]({entry["filename"]})\n' == original


def test_read_index_fails_loud_on_malformed_pointer(tmp_path):
    mem = tmp_path / ".claude" / "projects" / "malformed" / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text(
        "## Entries\n\n- [valid](valid.md)\n- [missing close](broken.md\n"
    )
    (mem / "valid.md").write_text("Valid.\n")

    result = _run(READ_INDEX, "malformed", home=tmp_path)
    assert result.returncode != 0
    data = json.loads(result.stdout)
    assert data["entries"] == []
    assert "line 4" in data["error"]


def test_read_index_fails_loud_on_grouped_pointer_line(tmp_path):
    """A list line packing several links behind a label is not prose.

    The climate-finance-het index was once regrouped as ``- Guards: [a](a.md),
    [b](b.md), …``; the reader skipped those lines as prose and returned 1 of 179
    entries, which step 6 would have written back as the whole index.
    """
    mem = tmp_path / ".claude" / "projects" / "grouped" / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text(
        "## Entries\n\n- [valid](valid.md)\n- Guards: [a](a.md), [b](b.md)\n"
    )
    for name in ("valid", "a", "b"):
        (mem / f"{name}.md").write_text("Body.\n")

    result = _run(READ_INDEX, "grouped", home=tmp_path)
    assert result.returncode != 0
    data = json.loads(result.stdout)
    assert data["entries"] == []
    assert "line 4" in data["error"]


def test_read_index_fails_loud_on_two_links_on_a_pointer_line(tmp_path):
    """The greedy title capture would read ``[a](a.md), [b](b.md)`` as one entry."""
    mem = tmp_path / ".claude" / "projects" / "twolinks" / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("## Entries\n\n- [a](a.md), [b](b.md)\n")
    for name in ("a", "b"):
        (mem / f"{name}.md").write_text("Body.\n")

    result = _run(READ_INDEX, "twolinks", home=tmp_path)
    assert result.returncode != 0
    assert "line 3" in json.loads(result.stdout)["error"]


def test_every_project_index_parses_every_pointer_line(tmp_path):
    """End-to-end corpus guard: a lossy parser cannot shorten an index."""
    repo = Path(__file__).parent.parent
    projects = repo / "projects"
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "projects").symlink_to(projects, target_is_directory=True)

    indexes = sorted(projects.glob("*/memory/MEMORY.md"))
    assert indexes, "positive control: repository carries no memory indexes"
    for index in indexes:
        pointer_count = sum(
            bool(re.match(r"^-\s+(?:\[|.*\]\([^)]+\.md\))", line.strip()))
            for line in index.read_text().splitlines()
        )
        result = _run(READ_INDEX, index.parents[1].name, home=tmp_path)
        assert result.returncode == 0, f"{index}: {result.stdout} {result.stderr}"
        parsed_count = len(json.loads(result.stdout)["entries"])
        assert parsed_count == pointer_count, (
            f"{index}: parsed {parsed_count} of {pointer_count} pointer lines"
        )


def test_no_other_dream_script_carries_the_lossy_index_regex():
    old_shape = "[^\\]]+"
    offenders = [
        path.name
        for path in DREAM_DIR.glob("*.py")
        if path != READ_INDEX and old_shape in path.read_text()
    ]
    assert offenders == []


def test_skill_md_instructs_preserve_evolution():
    content = (DREAM_DIR / "SKILL.md").read_text()
    assert "evolution" in content.lower() or "preserve" in content.lower()


# Legacy instruction checks for primary-checkout restore, promotion provenance
# and classifier accounting were removed with that workflow. The helper tests
# below remain until its remaining consumers are retired by the v8 migration.


def test_commit_py_has_rollback_subcommand():
    assert "rollback" in COMMIT_PY.read_text()


# ── Leading-dash project names (ticket 0500) ──────────────────────────────────
#
# Every directory under ~/.claude/projects/ begins with '-' (-home-haduong--claude,
# …). argparse reads such a value as the start of an option, so an unprotected
# positional aborts with a usage dump before the script runs.


@pytest.mark.integration
def test_read_index_leading_dash_project(tmp_path):
    project = "-home-haduong--claude"
    memory = tmp_path / ".claude" / "projects" / project / "memory"
    memory.mkdir(parents=True)
    (memory / "MEMORY.md").write_text(
        "## Entries\n\n- [feedback_vim](feedback_vim.md) — vim\n"
    )
    (memory / "feedback_vim.md").write_text("User prefers vim.\n")
    result = _run(READ_INDEX, project, home=tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["project"] == project, "leading dash lost"
    assert len(data["entries"]) == 1


@pytest.mark.integration
def test_read_index_help_still_works(tmp_path):
    """The separator auto-insert must not eat -h."""
    result = _run(READ_INDEX, "--help", home=tmp_path)
    assert result.returncode == 0
    assert "project" in result.stdout


@pytest.mark.integration
def test_commit_leading_dash_project(tmp_path):
    """commit.py's `commit` verb takes the project as its first positional."""
    home = tmp_path
    idh = home / ".claude"
    project = "-home-haduong--claude"
    memory = idh / "projects" / project / "memory"
    memory.mkdir(parents=True)
    (memory / "MEMORY.md").write_text("## Entries\n")
    (home / ".idh").symlink_to(idh, target_is_directory=True)  # ticket 0982
    subprocess.run(["git", "init", "-b", "main", str(idh)], capture_output=True)
    for k, v in (
        ("user.email", "t@example.com"),
        ("user.name", "T"),
        ("commit.gpgsign", "false"),
    ):
        subprocess.run(["git", "-C", str(idh), "config", k, v], capture_output=True)
    result = _run(COMMIT_PY, "commit", project, "5", "3", home=home)
    assert result.returncode == 0, result.stderr
    log = subprocess.run(
        ["git", "-C", str(idh), "log", "--format=%s", "-1"],
        capture_output=True,
        text=True,
    )
    assert project in log.stdout, "commit message lost the project name"


def test_no_anthropic_import_in_scripts():
    for script in [READ_INDEX, COMMIT_PY]:
        source = script.read_text()
        assert "import anthropic" not in source, f"{script.name} imports anthropic"
        assert "from anthropic" not in source, f"{script.name} imports anthropic"
