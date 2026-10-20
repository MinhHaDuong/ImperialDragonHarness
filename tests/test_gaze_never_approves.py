"""Gaze reviews; verify-gate gates (ticket 1153, plan 1096 answer 5).

Gaze must never return, post or promise APPROVED: that word is a gate verdict,
ruled by `/verify-gate` on the head gaze reviewed.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAZE = (ROOT / "skills" / "gaze" / "SKILL.md").read_text(encoding="utf-8")


def _section(heading: str) -> str:
    body = GAZE.split(heading, 1)[1]
    return re.split(r"\n#{2,3} ", body, maxsplit=1)[0]


def test_result_enumeration_has_no_gate_verdict():
    result = _section("### 6. Return the review result")
    m = re.search(r"^result: (.+)$", result, re.MULTILINE)
    assert m, "gaze must declare its result enumeration"
    values = {v.strip() for v in m.group(1).split("|")}
    assert values == {"REVIEWED", "FINDINGS", "ESCALATE"}


def test_output_template_has_no_gate_verdict():
    template = GAZE.split("## /gaze result", 1)[1].split("```", 1)[0]
    result = re.search(r"^result: (.+)$", template, re.MULTILINE)
    assert result and "APPROVED" not in result.group(1)
    for gate_only in ("REROLL", "NEEDS-AUTHOR", "gate_session_id", "ruled_tip_sha"):
        assert gate_only not in template, gate_only


def test_gaze_states_it_never_approves_and_does_not_gate():
    assert "Gaze\nreviews; `/verify-gate` gates" in GAZE
    assert "never returns APPROVED" in GAZE
    assert "Does not run `/verify-gate`" in GAZE


def test_gaze_has_no_gate_phase_or_fix_loop():
    for gone in ("### 6. Gate", "## Branch on verdict", "## Fix-agent contract", "Embedded gate procedure"):
        assert gone not in GAZE, gone
    assert not (ROOT / "agents" / "gaze-pr-review.md").exists()


def test_verify_gate_remains_the_gate():
    gate = (ROOT / "skills" / "verify-gate" / "SKILL.md").read_text(encoding="utf-8")
    desc = gate.split("description:", 1)[1].splitlines()[0]
    assert "APPROVED" in desc and "REROLL" in desc
