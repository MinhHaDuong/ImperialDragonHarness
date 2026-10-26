"""Gaze phase 5 simplify is report-only, round 1, with a proportion question.

Ticket 1213: simplify ran every round, applied nothing, and never asked
whether a defence is worth its cost. Gaze now makes no commits; the coder
acts on simplify findings like panel findings.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
GAZE = (SKILLS / "gaze" / "SKILL.md").read_text(encoding="utf-8")  # inlined by conftest
PHASE5 = GAZE.split("### 5. Simplify", 1)[1].split("### External reviewer panel", 1)[0]


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_phase5_is_report_only_round_one():
    norm = _norm(PHASE5)
    assert "report-only" in norm
    assert "round 1" in norm.lower() and "grew materially" in norm
    for gone in ("commit and push fixes", "applies bounded fixes", "confirm the dispositions"):
        assert gone not in norm, gone


def test_phase5_brief_asks_the_proportion_question():
    norm = _norm(PHASE5)
    assert "no real actor" in norm
    assert re.search(r"lines, branches(,| and) tests", norm)


def test_gaze_makes_no_commits():
    norm = _norm(GAZE)
    assert "gaze makes no commits" in norm.lower()
    assert "simplify fixes" not in norm
    for path in SKILLS.glob("*/**/*.md"):
        text = _norm(path.read_text(encoding="utf-8"))
        assert "may have pushed fixes" not in text, path
