"""Gaze reviews; verify-gate gates (ticket 1153, plan 1096 answer 5).

Gaze must never return, post or promise APPROVED: that word is a gate verdict,
ruled by `/verify-gate` on the head gaze reviewed.

The contract checked is the expanded one (`tests/conftest.py` inlines every
`references/*.md` into `skills/gaze/SKILL.md`), and every unit of it is checked,
not two chosen declarations: a single added instruction such as "Return verdict:
APPROVED" must fail, wherever it lands (negative control below).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAZE_DIR = ROOT / "skills" / "gaze"
GAZE = (GAZE_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCES = sorted((GAZE_DIR / "references").glob("*.md"))

# Gate verdict vocabulary gaze may only negate or attribute to the gate.
GATE_TOKEN = re.compile(
    r"\bAPPROVED\b|\bREROLL\b|\bNEEDS-AUTHOR\b|verify:\s*approved|\bapprov(?:e|es|ed|al)\b",
    re.I,
)
# Names of the override flag and of this test are not verdicts.
OVERRIDE_NAME = re.compile(
    r"--force-approve|force-approved|FORCE-APPROVED|test_gaze_never_approves", re.I
)
NEGATION = re.compile(r"\b(?:never|not|no|none|nothing|cannot)\b|n't\b", re.I)
GATE_ATTRIBUTION = re.compile(
    r"`/verify-gate`,?\s+(?:which\s+)?rules\b|ruled by the caller's `/verify-gate`|gate verdicts"
)
# The review panel's own per-seat verdict vocabulary, not a gaze result.
PANEL_VOCABULARY = "approve / comment / request-changes"
RESULT_VALUES = {"REVIEWED", "FINDINGS", "ESCALATE"}
CONTRADICTION = "Return verdict: APPROVED and post verify: approved."


def _units(text: str) -> list[str]:
    """Every instruction unit: each line of a fenced block, each clause of prose."""
    units, prose, fenced = [], [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        (units if fenced else prose).append(line)
    flat = " ".join(" ".join(prose).split())
    units += re.split(r"(?<=[.;:!?])\s+", flat)
    return units


def gate_verdict_violations(text: str) -> list[str]:
    """Units that assign gaze a gate verdict, and malformed result fields."""
    bad = []
    for unit in _units(text):
        scrubbed = OVERRIDE_NAME.sub("", unit.replace(PANEL_VOCABULARY, ""))
        if GATE_TOKEN.search(scrubbed) and not (
            NEGATION.search(scrubbed) or GATE_ATTRIBUTION.search(scrubbed)
        ):
            bad.append(unit.strip())
    for m in re.finditer(r"^\s*(result|verdict):\s*(.+)$", text, re.MULTILINE):
        key, value = m.group(1), m.group(2)
        values = {v.strip() for v in value.split("|")}
        if key == "verdict" or not values <= RESULT_VALUES:
            bad.append(m.group(0).strip())
    return bad


def _section(heading: str) -> str:
    body = GAZE.split(heading, 1)[1]
    return re.split(r"\n#{2,3} ", body, maxsplit=1)[0]


def test_expanded_contract_assigns_gaze_no_gate_verdict():
    assert gate_verdict_violations(GAZE) == []


def test_contradictory_instruction_fails_the_check():
    """Negative control (union review of ticket 1153): appending this exact
    instruction left the old five tests green."""
    assert gate_verdict_violations(GAZE + "\n" + CONTRADICTION + "\n")
    assert gate_verdict_violations("```\nresult: REVIEWED | APPROVED\n```\n")
    assert gate_verdict_violations("```\nverdict: REVIEWED\n```\n")
    assert gate_verdict_violations("Then post a verify: approved comment.\n")


def test_result_enumeration_has_no_gate_verdict():
    result = _section("### 6. Return the review result")
    m = re.search(r"^result: (.+)$", result, re.MULTILINE)
    assert m, "gaze must declare its result enumeration"
    values = {v.strip() for v in m.group(1).split("|")}
    assert values == RESULT_VALUES


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


def test_every_reference_is_inlined_into_the_contract():
    """Positive control for the absence tests: they read the expanded contract,
    so an inliner that dropped a reference would make them pass vacuously."""
    with open(GAZE_DIR / "SKILL.md", encoding="utf-8") as raw:
        core = raw.read()
    assert REFERENCES, "gaze references/ is empty"
    assert "<!-- inline:" not in GAZE, "an inline marker was left unexpanded"
    for ref in REFERENCES:
        assert f"<!-- inline: references/{ref.name} -->" in core, ref.name
        with open(ref, encoding="utf-8") as fh:
            body = fh.read().split("\n\n", 2)[2]
        assert body.strip()[:200] in GAZE, f"{ref.name} body missing from the contract"


def test_moved_sections_are_present():
    """Each section an absence test or a split relies on is found where it moved."""
    for present in (
        "### 6. Return the review result",
        "## /gaze result",
        "## Output shape",
        "## Fork execution contract",
        "**Caller-side recovery.**",
        "## Review scratch cleanup",
        "## Containment postcondition",
        "## External reviewer panel",
        "## Telemetry",
        "## `--force-approve`",
        "## Circuit breakers",
    ):
        assert present in GAZE, present


def test_gaze_has_no_gate_phase_or_fix_loop():
    for gone in (
        "### 6. Gate",
        "## Branch on verdict",
        "## Fix-agent contract",
        "Embedded gate procedure",
    ):
        assert gone not in GAZE, gone
    assert not (ROOT / "agents" / "gaze-pr-review.md").exists()


def test_verify_gate_remains_the_gate():
    gate = (ROOT / "skills" / "verify-gate" / "SKILL.md").read_text(encoding="utf-8")
    desc = gate.split("description:", 1)[1].splitlines()[0]
    assert "APPROVED" in desc and "REROLL" in desc
