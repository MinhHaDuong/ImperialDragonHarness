"""Exact tool-grant facts behind ticket 1167.

A 14-day transcript scan found 74 "No such tool available: Skill" failures: a
profile told the delegate to call Skill while its agent definition did not
grant it. The suspected cause was one missing grant plus three profiles that assumed it.
These checks pin those facts without parsing prose; a prose lint was tried and
withdrawn after two independent reviews kept defeating it (see ticket 1167's
log and the structured-declaration follow-up).
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]

# Seats whose profile says "You have no Skill tool" must not be granted it.
READ_ONLY_SEATS = ("code-reviewer", "gate-seat", "prose-reviewer")


def granted(agent: str) -> set[str]:
    text = (REPO / "agents" / f"{agent}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"agents/{agent}.md has no frontmatter block"
    m = re.search(r"^tools:\s*(.+)$", text.split("---", 2)[1], re.M)
    assert m, f"agents/{agent}.md has no tools: line"
    return {t.strip() for t in m.group(1).split(",")}


def test_adherence_seat_grants_skill():
    """Its profile makes invoking verify-adherence the first action."""
    assert "Skill" in granted("adherence-seat")


@pytest.mark.parametrize("seat", READ_ONLY_SEATS)
def test_seat_without_skill_says_so(seat):
    """The profile's substitute sentence and the grant must agree."""
    profile = (REPO / "profiles" / seat / "PROFILE.md").read_text(encoding="utf-8")
    assert "Skill" not in granted(seat)
    assert "You have no Skill tool: read that file with Read." in profile
