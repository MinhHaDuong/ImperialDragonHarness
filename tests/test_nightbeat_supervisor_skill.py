"""Adherence tests for nightbeat-supervisor SKILL.md — commit discipline."""

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "nightbeat-supervisor"
    / "SKILL.md"
)


def _read_skill() -> str:
    return SKILL.read_text()


def test_clean_tree_guard_present():
    text = _read_skill()
    assert "git status --porcelain" in text


def test_tracked_write_points_have_commit():
    text = _read_skill()
    write_markers = [
        "settings.json` allowlist",
        "raise the per-project `ProjectConfig`",
        "raid_timeout_s` in the per-project",
        "split into one ticket",
        "open a ticket stating the root cause",
        "REROLL → append the failing criteria",
        "Create a\nticket with the verdict",
    ]
    for marker in write_markers:
        idx = text.find(marker)
        assert idx != -1, f"write-point marker not found: {marker}"
        surrounding = text[idx : idx + 400]
        assert re.search(r"git (add|commit)", surrounding), (
            f"no commit instruction near write point: {marker}"
        )


def test_commit_principle_declared():
    text = _read_skill()
    assert "Commit tracked writes immediately" in text


def test_self_modification_guard_is_an_invariant():
    """The read-only-own-definitions guard must be binding, not advisory.

    It belongs inside the Invariants section, so an executor cannot edit skill
    definition files mid-run while remaining formally compliant.
    """
    text = _read_skill()
    start = text.find("## Invariants (the only prescriptions)")
    assert start != -1, "Invariants section header missing"
    end = text.find("## Executor's latitude", start)
    assert end != -1, "Executor's latitude section missing"
    invariants = " ".join(text[start:end].split())
    assert "skill definition files" in invariants, (
        "self-modification guard not inside the Invariants section"
    )
    assert "read-only" in invariants
