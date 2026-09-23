"""The review pipeline must invoke the checkout guard before a verdict."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_family_invokes_anchor():
    for name in ("review-pr", "review-pr-prose", "gaze"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text()
        assert "scripts/review-pr-anchor.py" in text
        assert "REVIEW-ANCHOR:" in text


def test_builtin_review_rejects_unverified_empty_result():
    text = (ROOT / "skills/gaze/SKILL.md").read_text()
    agent_b = text.split("**Agent B — built-in review**", 1)[1].split(
        "**Agent C — PR review**", 1
    )[0]
    assert agent_b.count("scripts/review-pr-anchor.py") >= 1
    assert "then runs the same anchor command again" in agent_b
    assert "empty-diff answer" in agent_b
    assert "review: FAILED" in agent_b
