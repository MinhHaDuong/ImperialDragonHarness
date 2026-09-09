"""Adherence test for the root-cause taxonomy (ticket 0291).

The five-way error taxonomy (arXiv:2604.21965 §5.3, reframed for the harness)
labels verify-gate's REROLL/ESCALATE verdicts: the SKILL.md must declare the
field, document the taxonomy section, and carry the exact five category tokens.

**It was a convention shared with skill-doctor, and is no longer.** Ticket 0885
removed that skill, so this guards one holder rather than the agreement of two.
Say plainly what that costs: cross-file drift is no longer detectable here,
because there is no second file to drift from. What survives is worth keeping
on its own — a taxonomy that silently loses a category, or renames one, is a
real defect, and the five tokens below are the fixed point that catches it.

Should a second holder appear, add it to a HOLDERS tuple and restore the
cross-file assertion; the shape of that test is in this file's history.
"""

from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"
VERIFY_GATE = SKILLS / "verify-gate" / "SKILL.md"

TOKENS = {
    "**Agent Error**",
    "**Extractor Error**",
    "**Original Error**",
    "**Missing Data**",
    "**Other**",
}


def _taxonomy_tokens(text: str) -> set[str]:
    """Extract the bolded five-token set from a file's taxonomy section."""
    return {tok for tok in TOKENS if tok in text}


@pytest.mark.adherence
def test_verify_gate_file_exists():
    """The corpus guard: every assertion below reads this one file, so its
    absence would turn the rest green over nothing."""
    assert VERIFY_GATE.is_file(), f"{VERIFY_GATE} missing — the other tests here assert nothing without it"


@pytest.mark.adherence
def test_verify_gate_declares_field():
    text = VERIFY_GATE.read_text()
    assert "root_cause_class:" in text, "verify-gate verdict shape must carry root_cause_class"


@pytest.mark.adherence
def test_verify_gate_has_taxonomy_heading():
    text = VERIFY_GATE.read_text()
    assert "## Root-cause taxonomy" in text, "verify-gate must document the taxonomy"


@pytest.mark.adherence
def test_verify_gate_contains_all_five_tokens():
    found = _taxonomy_tokens(VERIFY_GATE.read_text())
    assert found == TOKENS, f"{VERIFY_GATE.name} missing tokens: {TOKENS - found}"
