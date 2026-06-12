"""review-pr-prose documents the editorial-brief auditor (ticket 0253).

The skill must check manuscript diffs against an optional per-project
editorial-brief file: default location ``docs/editorial-brief.md``,
graceful skip when the file is absent, and per-entry verdicts
(upheld / violated / not touched by this diff). This ratchet pins the
documented contract in the skill text — companion to AEDIST 0557, which
moves positive prose literals out of CI and into review-time judgment.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "review-pr-prose" / "SKILL.md"


def skill_text() -> str:
    with open(SKILL) as f:
        return f.read()


def test_documents_default_brief_location():
    assert "docs/editorial-brief.md" in skill_text(), (
        "review-pr-prose must document the default editorial-brief location "
        "docs/editorial-brief.md (ticket 0253)"
    )


def test_documents_graceful_degradation_when_brief_absent():
    text = skill_text().lower()
    assert "absent" in text or "skip" in text, (
        "review-pr-prose must document that the editorial-brief check is "
        "skipped when the file is absent (skills-degrade-gracefully rule)"
    )


def test_documents_per_entry_verdicts():
    text = skill_text().lower()
    for verdict in ("upheld", "violated", "not touched"):
        assert verdict in text, (
            f"review-pr-prose must document the per-entry verdict {verdict!r} "
            "(upheld / violated / not touched by this diff)"
        )
