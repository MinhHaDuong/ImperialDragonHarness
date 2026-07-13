"""Guard: verify-adherence must wire the trace-based path-access scan (ticket 0289).

Child of tracker 0266 (pillage manifest, technique 1). The path-access scan
(scripts/trace-path-scan.py) is a mechanical verify-adherence phase; its
SKILL.md wiring must not drift into a paraphrase the way raid Phase 5 and hunt
step 11 once did. Text-grep only → fast tier, no marker.
"""

from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent / "skills" / "verify-adherence" / "SKILL.md"


@pytest.mark.parametrize(
    "needle,reason",
    [
        (
            "### 1.2 Path-access",
            "verify-adherence SKILL.md must document the path-access scan as phase 1.2",
        ),
        (
            "scripts/trace-path-scan.py",
            "verify-adherence SKILL.md must invoke scripts/trace-path-scan.py",
        ),
        (
            "skip phase 1.2",
            "verify-adherence SKILL.md circuit breakers must state that a missing "
            "trace= argument skips phase 1.2 silently",
        ),
    ],
)
def test_skill_wires_path_scan(needle, reason):
    assert needle in SKILL.read_text(), reason
