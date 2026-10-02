"""Memory v8 pilot structure and relocated-clone readability (ticket 0920).

The pilot activates the v8 convention in this repository itself: a bounded
index, themes with provenance, the annual journal, and the inventoried
sources left at their original paths. The integration test proves the first
exit criterion mechanically: a clone relocated away from its origin checkout,
with its origin remote removed and no harness installed, reads the whole
memory surface through relative links alone.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MEMORY = REPO / "memory"
INDEX = MEMORY / "MEMORY.md"

# The ten tracked memory/ root sources inventoried by 0917 in
# docs/memory-v8/source-inventory.md (PR #1102). Old-path correspondence:
# the pilot links these sources but never moves or rewrites them.
PILOT_SOURCES = (
    "MEMORY.md",
    "feedback_rules_come_from_memory_consolidation.md",
    "feedback_subagent_model_effort_levers.md",
    "reference_branch_cleanup_incidents.md",
    "reference_git_in_a_worktree_session.md",
    "reference_zotero.md",
    "journal/2026/2026-10-01-memory-helper-retirement.md",
    "journal/2026/2026-10-01-memory-v8-design-and-boundaries.md",
    "journal/2026/2026-10-01-portable-registration-review.md",
    "journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md",
)

# The four reference notes the legacy index linked. Correspondence requires
# the v8 surface (index or themes) to keep linking each of them.
LEGACY_INDEX_LINKS = (
    "reference_zotero.md",
    "feedback_subagent_model_effort_levers.md",
    "reference_git_in_a_worktree_session.md",
    "reference_branch_cleanup_incidents.md",
)

LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")


def relative_links(text):
    """Markdown link targets that are repo-relative (scheme-less)."""
    return [
        target
        for target in LINK.findall(text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]


def unresolved_links(root, doc):
    """Relative links in ``doc`` that do not resolve inside ``root``."""
    broken = []
    for target in relative_links(doc.read_text(encoding="utf-8")):
        resolved = (doc.parent / target).resolve()
        if not resolved.is_relative_to(root.resolve()):
            broken.append(f"{target} (escapes the clone)")
        elif not resolved.is_file():
            broken.append(target)
    return broken


def test_index_is_bounded_and_terminated():
    text = INDEX.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 100
    assert text.endswith("\n")


def test_pilot_sources_stay_at_inventory_paths():
    for rel in PILOT_SOURCES:
        assert (MEMORY / rel).is_file(), rel


def test_v8_surface_links_sources_and_journal():
    surface = [INDEX, *sorted((MEMORY / "topics").glob("*.md"))]
    assert surface
    combined = "".join(p.read_text(encoding="utf-8") for p in surface)
    for name in LEGACY_INDEX_LINKS:
        assert f"({name})" in combined, name
    assert "journal/2026/" in combined
    assert not unresolved_links(REPO, INDEX)
    for doc in surface:
        assert not unresolved_links(REPO, doc)


def test_topics_cite_provenance():
    topics = sorted((MEMORY / "topics").glob("*.md"))
    assert topics
    for topic in topics:
        text = topic.read_text(encoding="utf-8")
        assert (
            "source-revisions.tsv" in text or "source-inventory.md" in text
        ), topic.name
        assert any(
            (topic.parent / target).is_file()
            for target in relative_links(text)
        ), topic.name


def test_agents_md_merges_memory_reading_section():
    text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    assert "[memory/MEMORY.md](memory/MEMORY.md)" in text


@pytest.mark.integration
def test_relocated_clone_remains_readable(tmp_path):
    """Exit criterion 1: a moved clone reads without origin home or harness.

    Clone the repository, move the clone elsewhere, drop the origin remote —
    then read the memory surface with plain file access only: every relative
    link in the index and the themes must resolve inside the relocated clone.
    """
    checkout = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(checkout)],
        check=True,
    )
    relocated = tmp_path / "elsewhere" / "moved-clone"
    relocated.parent.mkdir()
    shutil.move(str(checkout), str(relocated))
    subprocess.run(
        ["git", "-C", str(relocated), "remote", "remove", "origin"],
        check=True,
    )

    clone_index = relocated / "memory" / "MEMORY.md"
    assert clone_index.is_file()
    docs = [clone_index, *sorted((relocated / "memory" / "topics").glob("*.md"))]
    for doc in docs:
        broken = unresolved_links(relocated, doc)
        assert not broken, f"{doc}: {broken}"
