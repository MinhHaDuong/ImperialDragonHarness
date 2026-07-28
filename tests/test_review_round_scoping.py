"""Pin round scoping across the review skills (ticket 0377).

Review panels were the largest subagent cost bucket in the 2026-07-28 trace
analysis (44–56% of all subagent output tokens) because round pricing was flat:
round N re-ran every perspective even when round N−1 gave most perspectives
nothing to say. Ticket 0377 scopes later rounds to the perspectives that
objected, plus one cheap regression check.

Two mechanisms had to change together:

- `skills/review-pr/SKILL.md` gains a § Round scoping rule (round 1 = full
  proportional panel; round N>1 = objecting perspectives + regression check),
  and relates it to gaze's Convergence mode so the two are not confused.
- `skills/gaze/SKILL.md` drops the #562 clause that sent *any* round ≥ 2 to
  the full battery unconditionally, replacing it with a reset condition tied
  to substantial diff rewrite.

Polarity: the negative guards pin the OLD phrasing and may be exact — that
wording is gone and must not come back. The positive markers stay LOOSE
(section name only), so the prose can be rewritten without breaking the test.

RED proof (2026-07-28): against the unedited SKILL.md files all four tests
failed — gaze still carried both old clauses and neither skill had a
"Round scoping" section.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
GAZE = REPO / "skills" / "gaze" / "SKILL.md"
REVIEW_PR = REPO / "skills" / "review-pr" / "SKILL.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_gaze_no_longer_forces_full_battery_every_round():
    text = _text(GAZE)
    assert "unconditionally any round" not in text, (
        "skills/gaze/SKILL.md still sends any round >= 2 to the full battery "
        "unconditionally. Ticket 0377 replaced the #562 clause: a round >= 2 "
        "reruns a scoped battery, and only a substantial diff rewrite resets "
        "to the full panel."
    )
    assert "regardless of diff size" not in text, (
        "skills/gaze/SKILL.md still claims a REROLL escalates to the full "
        "battery regardless of diff size (ticket 0377 removed that clause)."
    )


def test_gaze_has_round_scoping_section():
    assert "Round scoping" in _text(GAZE), (
        "skills/gaze/SKILL.md must carry a 'Round scoping' section stating "
        "what a round >= 2 re-runs and when scoping resets (ticket 0377)."
    )


def test_review_pr_has_round_scoping_section():
    assert "Round scoping" in _text(REVIEW_PR), (
        "skills/review-pr/SKILL.md must carry a 'Round scoping' section: "
        "round 1 runs the full proportional panel, later rounds re-run only "
        "the perspectives that objected (ticket 0377)."
    )


def test_review_pr_round_scoping_relates_to_convergence():
    assert "convergence" in _text(REVIEW_PR).lower(), (
        "skills/review-pr/SKILL.md's round scoping must be related to gaze's "
        "Convergence mode (ticket 0315), so callers do not confuse "
        "within-invocation scoping with caller-level repeat suppression "
        "(ticket 0377)."
    )
