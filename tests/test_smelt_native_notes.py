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
