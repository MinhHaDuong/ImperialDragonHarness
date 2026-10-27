"""Yawn's action-plan contract headings stay unique: /molt reads the plan
by its **fix-now**, **open-ticket** and **skip** headings."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YAWN = ROOT / "skills/yawn/SKILL.md"


def test_contract_headings_untouched():
    text = YAWN.read_text()
    for heading in ("**fix-now**", "**open-ticket**", "**skip**"):
        assert text.count(f"\n{heading}\n") == 1
