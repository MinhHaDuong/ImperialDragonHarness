"""Simplify is a report-only perspective with a proportion question.

Ticket 1213: simplify ran every round, applied nothing, and never asked
whether a defence is worth its cost. Ticket 1225: it is a perspective gaze's
plan may choose, not a fixed phase. Gaze makes no commits; the coder acts on
simplify findings like any other.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
GAZE = (SKILLS / "gaze" / "SKILL.md").read_text(encoding="utf-8")  # inlined by conftest
SIMPLIFY = GAZE.split("**Simplify**", 1)[1].split("**Rules**", 1)[0]


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_simplify_is_report_only():
    assert "report-only" in _norm(SIMPLIFY)


def test_simplify_asks_the_proportion_question():
    norm = _norm(SIMPLIFY)
    assert "no real actor" in norm
    assert re.search(r"lines, branches(,| and) tests", norm)


def test_gaze_makes_no_commits():
    norm = _norm(GAZE)
    assert "gaze makes no commits" in norm.lower()
