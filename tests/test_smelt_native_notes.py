"""Listing of Claude Code native memory notes for a smelt run (ticket 1350)."""
import importlib.util
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "smelt_native_notes", Path(__file__).resolve().parents[1] / "scripts/smelt_native_notes.py"
)
native = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = native
SPEC.loader.exec_module(native)


def test_store_path_encodes_project_like_claude_code(tmp_path):
    got = native.store_path(Path("/home/u/.agents"), home=tmp_path)
    assert got == tmp_path / ".claude/projects/-home-u--agents/memory"


def test_list_notes_reads_frontmatter_and_skips_index(tmp_path):
    (tmp_path / "MEMORY.md").write_text("- [a](a.md)\n")
    (tmp_path / "a.md").write_text(
        "---\nname: a\ndescription: Do the thing\nmetadata:\n  type: feedback\n---\nbody\n")
    (tmp_path / "b.md").write_text("no frontmatter\n")
    rows = native.list_notes(tmp_path)
    assert [r["file"] for r in rows] == ["a.md", "b.md"]
    assert rows[0]["description"] == "Do the thing"
    assert rows[0]["type"] == "feedback"
    assert rows[1]["description"] == ""
    assert len(rows[0]["sha"]) == 40


def test_missing_store_is_reported_not_created(tmp_path):
    with pytest.raises(FileNotFoundError):
        native.list_notes(tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


@pytest.mark.integration
def test_worktree_path_resolves_to_primary_store(tmp_path):
    import subprocess
    primary = tmp_path / "repo"
    primary.mkdir()
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(g + ["init", "-q", str(primary)], check=True)
    subprocess.run(g + ["-C", str(primary), "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    wt = tmp_path / "wt"
    subprocess.run(g + ["-C", str(primary), "worktree", "add", "-q", str(wt)], check=True)
    assert native.primary_checkout(wt) == primary.resolve()
    assert native.primary_checkout(primary) == primary.resolve()
    assert native.store_path(native.primary_checkout(wt), home=tmp_path) == \
        native.store_path(primary.resolve(), home=tmp_path)


def test_non_git_path_is_left_as_given(tmp_path):
    assert native.primary_checkout(tmp_path) == tmp_path.resolve()
