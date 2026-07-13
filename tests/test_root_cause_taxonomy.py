"""Adherence test for the shared root-cause taxonomy (ticket 0291).

The five-way error taxonomy (arXiv:2604.21965 §5.3, reframed for the harness)
is a labeling convention shared by verify-gate's REROLL/ESCALATE verdicts and
skill-doctor's per-pattern diagnoses. This guards the convention: both SKILL.md
files must declare the field, document the taxonomy section, and agree on the
exact five category tokens.
"""

from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"
VERIFY_GATE = SKILLS / "verify-gate" / "SKILL.md"
SKILL_DOCTOR = SKILLS / "skill-doctor" / "SKILL.md"

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
def test_verify_gate_declares_field():
    text = VERIFY_GATE.read_text()
    assert "root_cause_class:" in text, "verify-gate verdict shape must carry root_cause_class"


@pytest.mark.adherence
def test_verify_gate_has_taxonomy_heading():
    text = VERIFY_GATE.read_text()
    assert "## Root-cause taxonomy" in text, "verify-gate must document the taxonomy"


@pytest.mark.adherence
def test_skill_doctor_report_table_has_root_cause_column():
    text = SKILL_DOCTOR.read_text()
    header = next((ln for ln in text.splitlines() if "| Rank |" in ln), None)
    assert header is not None, "skill-doctor report table header not found"
    assert "Root Cause" in header, "skill-doctor report table must have a Root Cause column"


@pytest.mark.adherence
def test_skill_doctor_has_taxonomy_heading():
    text = SKILL_DOCTOR.read_text()
    assert "### Root-cause taxonomy" in text, "skill-doctor must document the taxonomy"


@pytest.mark.adherence
def test_both_files_contain_all_five_tokens():
    # Each file's set is checked against the fixed TOKENS constant, which also
    # proves cross-file consistency (both sets equal TOKENS, so they equal
    # each other) — a separate equality test would be a tautology.
    for path in (VERIFY_GATE, SKILL_DOCTOR):
        found = _taxonomy_tokens(path.read_text())
        assert found == TOKENS, f"{path.name} missing tokens: {TOKENS - found}"
