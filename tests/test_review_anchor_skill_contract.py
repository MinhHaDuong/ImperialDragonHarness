"""The review pipeline must invoke the checkout guard before a verdict."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_family_invokes_anchor():
    for name in ("review-pr", "review-pr-prose", "gaze"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text()
        assert "scripts/review-pr-anchor.py" in text
        assert "REVIEW-ANCHOR:" in text
