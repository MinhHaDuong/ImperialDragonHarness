"""A split skill is only as good as its pointers.

Carving a SKILL.md into a router plus `references/*.md` trades one long body
for a short one and a read. That trade is sound exactly while the pointers
hold: a router naming a file that no longer exists sends the agent to a dead
read and it proceeds on the router alone — with the contract details that made
the subcommand correct silently absent. Nothing errors, and the failure looks
like a model that ignored instructions.

The reverse is the same defect: a reference file nothing points at is text that
will never be read, drifting away from the skill it documents.

Generic over `skills/*/`, so the next split is covered without a code change.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"

POINTER = re.compile(r"`references/([\w.-]+\.md)`")


def split_skills() -> list[Path]:
    """Skill directories that carry a references/ subdirectory."""
    return sorted(p.parent for p in SKILLS.glob("*/references") if p.is_dir())


def skill_corpus(root: Path) -> list[Path]:
    return [root / "SKILL.md", *sorted((root / "references").glob("*.md"))]


def pointers(root: Path) -> set[str]:
    found = set()
    for md in skill_corpus(root):
        found.update(POINTER.findall(md.read_text(encoding="utf-8")))
    return found


def test_at_least_one_skill_is_split():
    """Positive control: without a subject, every assertion below is vacuous.

    Both loops iterate over globs. If `skills/*/references` stops matching —
    a renamed convention, a moved tree — the two tests pass by iterating over
    nothing, and report a clean bill of health for a check that never ran.
    """
    assert split_skills(), (
        "no skill has a references/ directory: either the split convention was "
        "abandoned, or this file's glob no longer finds it and both checks "
        "below are passing on an empty set"
    )


@pytest.mark.parametrize("root", split_skills(), ids=lambda p: p.name)
def test_every_pointer_resolves(root: Path):
    missing = sorted(t for t in pointers(root) if not (root / "references" / t).is_file())
    assert not missing, (
        f"{root.name} points at {missing} under references/, which does not "
        "exist — the agent reads the router, the read fails, and it proceeds "
        "without the contract that file was carrying"
    )


@pytest.mark.parametrize("root", split_skills(), ids=lambda p: p.name)
def test_every_reference_file_is_pointed_at(root: Path):
    named = pointers(root)
    orphans = sorted(p.name for p in (root / "references").glob("*.md") if p.name not in named)
    assert not orphans, (
        f"{root.name} carries {orphans} under references/ that nothing names: "
        "text that will never be read drifts from the skill it documents"
    )
