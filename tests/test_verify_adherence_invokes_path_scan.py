"""Guard: verify-adherence must wire the trace-based path-access scan (ticket 0289).

Child of tracker 0266 (pillage manifest, technique 1). The path-access scan
(scripts/trace-path-scan.py) is a mechanical verify-adherence phase; its
SKILL.md wiring must not drift into a paraphrase the way raid Phase 5 and hunt
step 11 once did. Text-grep only → fast tier, no marker.
"""

from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "verify-adherence" / "SKILL.md"


def test_skill_documents_path_scan_phase():
    text = SKILL.read_text()
    assert "### 1.2 Path-access" in text, (
        "verify-adherence SKILL.md must document the path-access scan as phase 1.2"
    )


def test_skill_names_the_detector_script():
    text = SKILL.read_text()
    assert "scripts/trace-path-scan.py" in text, (
        "verify-adherence SKILL.md must invoke scripts/trace-path-scan.py"
    )


def test_skill_has_trace_circuit_breaker():
    text = SKILL.read_text()
    assert "skip phase 1.2" in text, (
        "verify-adherence SKILL.md circuit breakers must state that a missing "
        "trace= argument skips phase 1.2 silently"
    )
