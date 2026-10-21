"""review-pr-prose names the editorial brief that a rule points at (ticket 0253).

``rules/prose-adherence-tests.md`` sends positive prose intent to
``docs/editorial-brief.md``, checked at review time by /review-pr-prose. The
pointer holds only while the skill names that default location.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "review-pr-prose" / "SKILL.md"


def test_documents_default_brief_location():
    assert "docs/editorial-brief.md" in SKILL.read_text(), (
        "review-pr-prose must document the default editorial-brief location "
        "docs/editorial-brief.md (ticket 0253)"
    )
