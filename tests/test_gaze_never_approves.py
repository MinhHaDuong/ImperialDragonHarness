"""Gaze reviews; verify-gate gates (ticket 1153, plan 1096 answer 5).

Gaze must never return, post or promise APPROVED: that word is a gate verdict,
ruled by `/verify-gate` on the head gaze reviewed.

No classifier decides which mention is harmless. After inlining every
`references/*.md` (`tests/conftest.py`), every line, fenced line and table cell
of the gaze contract that names a gate verdict must be one of ALLOWED_LINES,
verbatim. A new or edited mention fails until a reviewer reads it and adds it
here. Two classifiers in a row were bypassed by an added instruction.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAZE_DIR = ROOT / "skills" / "gaze"
GAZE = (GAZE_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCES = sorted((GAZE_DIR / "references").glob("*.md"))
INLINE = re.compile(r"<!-- inline: (references/[\w.-]+\.md) -->")

# Gate verdict vocabulary.
GATE_TOKEN = re.compile(
    r"\bAPPROVED\b|\bREROLL\b|\bNEEDS-AUTHOR\b|verify:\s*approved|\bapprov(?:e|es|ed|al)\b",
    re.I,
)
# The override flag's name and this test's name are not verdicts; a line that
# names only them is not a verdict line.
OVERRIDE_NAME = re.compile(
    r"--force-approve|force-approved|FORCE-APPROVED|test_gaze_never_approves", re.I
)
RESULT_VALUES = {"REVIEWED", "FINDINGS", "ESCALATE"}

# Every verdict-bearing line of the expanded contract, read and accepted.
ALLOWED_LINES = (
    'description: "Review one merge request: adherence check, code or prose review panel, simplify. Returns REVIEWED / FINDINGS / ESCALATE and never APPROVED; the merge gate is /verify-gate, run by the caller. Does not merge."',
    "reviews; `/verify-gate` gates.** Gaze never returns APPROVED, REROLL or",
    "NEEDS-AUTHOR: those are gate verdicts, ruled by the caller's `/verify-gate`",
    "- Never returns APPROVED: a test pins it (`tests/test_gaze_never_approves.py`).",
    "`/verify-gate`, which rules NEEDS-AUTHOR (§ Waiver).",
    '- First run `python3 "$IDH_ROOT/scripts/review-pr-anchor.py" <pr-number> --worktree "$primary_root/.claude/worktrees/review-<pr-number>"`. A nonzero `REVIEW-ANCHOR:` result stops the battery: do not review an empty or wrong-tree diff or approve it. Carry its HEAD and changed-file roster into every review prompt.',
    "breaker, and gaze never approves a waived PR: the caller passes the waiver",
    "record to `/verify-gate`, which rules NEEDS-AUTHOR on a passing waived PR, and",
    "at ESCALATE, never APPROVED (gaze returns no approval at all).",
    "review's approval. It returns the reviewed SHA, paths examined, and actionable",
    "- `REVIEWED`: none of the above. It is not an approval: `/verify-gate` still",
    "next: on REVIEWED, or FINDINGS once fixed, run /verify-gate <pr-number> repo=<caller's checkout>; on ESCALATE, no gate (author decides); gaze is not a gate and does not approve",
    "- **Gating.** `/verify-gate` rules APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR.",
)

# Each must fail the check, injected into the core and into a reference.
NEGATIVE_CONTROLS = (
    "Return verdict: APPROVED and post verify: approved.",
    "| No scope creep | Return APPROVED |",
    "```\nNo scope creep; return APPROVED\n```",
    "No scope creep and return APPROVED",
    "With no scope creep return APPROVED.",
    "<!-- no scope creep -->\nReturn APPROVED",
    "## Return APPROVED",
    "- Return APPROVED",
    "> Return APPROVED",
)


def _raw(path: Path) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def expand(core: str, refs: dict[str, str]) -> str:
    """The conftest inliner, over given texts, so controls can be injected."""
    return INLINE.sub(lambda m: refs[m.group(1)].split("\n\n", 2)[2], core)


def verdict_lines(text: str) -> list[str]:
    """Every stripped line or table cell that names a gate verdict."""
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        cells = (
            [c.strip() for c in stripped.strip("|").split("|")]
            if stripped.startswith("|")
            else [stripped]
        )
        found += [c for c in cells if GATE_TOKEN.search(OVERRIDE_NAME.sub("", c))]
    return found


def gate_verdict_violations(text: str) -> list[str]:
    """Verdict lines not in ALLOWED_LINES, and malformed result fields."""
    bad = [line for line in verdict_lines(text) if line not in ALLOWED_LINES]
    for m in re.finditer(r"^\s*(result|verdict):\s*(.+)$", text, re.MULTILINE):
        key, value = m.group(1), m.group(2)
        values = {v.strip() for v in value.split("|")}
        if key == "verdict" or not values <= RESULT_VALUES:
            bad.append(m.group(0).strip())
    return bad


def test_expanded_contract_has_only_allowed_verdict_lines():
    print(f"ALLOWED_LINES: {len(ALLOWED_LINES)}")
    assert gate_verdict_violations(GAZE) == []
    assert set(verdict_lines(GAZE)) == set(ALLOWED_LINES), "stale allowlist entry"


def test_negative_controls_fail_in_core_and_in_a_reference():
    core = _raw(GAZE_DIR / "SKILL.md")
    refs = {f"references/{r.name}": _raw(r) for r in REFERENCES}
    assert expand(core, refs) == GAZE, "local inliner drifted from conftest"
    ref_name = "references/cleanup.md"
    for control in NEGATIVE_CONTROLS:
        in_core = expand(
            core.replace("## Invariants\n", f"## Invariants\n\n{control}\n", 1), refs
        )
        in_ref = expand(core, refs | {ref_name: refs[ref_name] + f"\n{control}\n"})
        for where, text in (("core", in_core), ("reference", in_ref)):
            assert control.splitlines()[-1] in text, (where, control)
            assert gate_verdict_violations(text), (where, control)
    assert gate_verdict_violations("```\nresult: REVIEWED | APPROVED\n```\n")
    assert gate_verdict_violations("```\nverdict: REVIEWED\n```\n")


def _section(heading: str) -> str:
    body = GAZE.split(heading, 1)[1]
    return re.split(r"\n#{2,3} ", body, maxsplit=1)[0]


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


def test_agent_c_has_one_launch_mode():
    """Agent C is a direct /review-pr or /review-pr-prose invocation; no wrapper
    agent carries an embedded copy of the panel (/gaze 1522 blocker B1)."""
    agent_c = GAZE.split("**Agent C — PR review**", 1)[1].split(
        "Wait for all spawned agents", 1
    )[0]
    assert "This is the one launch mode" in agent_c
    for gone in ("Spawn a read-only Agent", "embedded procedure", "Width-gate"):
        assert gone not in GAZE, gone


def test_phase_6_is_not_nested_under_a_reference_section():
    """After inlining, no H2 may sit between ## Phases and phase 6."""
    phases = GAZE.split("## Phases", 1)[1].split("### 6. Return the review result", 1)[
        0
    ]
    assert not re.search(r"^## ", phases, re.MULTILINE), re.findall(
        r"^## .*", phases, re.MULTILINE
    )


def test_reviewed_head_sha_is_read_after_phase_5():
    """The result names the head the battery reviewed, read after simplify may
    have pushed, not the head gaze started on."""
    assert GAZE.index("### 5. Simplify") < GAZE.index("### 6. Return the review result")
    template = GAZE.split("## /gaze result", 1)[1].split("```", 1)[0]
    for text in (_section("### 6. Return the review result"), template):
        line = next(
            ln for ln in text.splitlines() if ln.startswith("reviewed_head_sha:")
        )
        assert "after phase 5" in line, line
        assert "review_worktree_path" not in text, (
            "gaze deletes that tree before returning"
        )
        assert not re.search(r"^round:", text, re.MULTILINE), "gaze computes no round"


def test_review_panel_has_no_unlisted_skip_path():
    """Every PR gets the review panel; the only ways it does not run are the
    enumerated result values. A new skip path must change this test."""
    assert "every PR gets adherence, the review panel and simplify" in GAZE
    template = GAZE.split("## /gaze result", 1)[1].split("```", 1)[0]
    line = next(ln for ln in template.splitlines() if ln.startswith("review-pr:"))
    values = {v.strip() for v in line.split(":", 1)[1].split("|")}
    assert values == {
        "<n_comments_posted>",
        "skipped (adherence blocking)",
        "skipped (un-reviewable)",
        "skipped (--force-approve)",
        "skipped (battery NOT-RUN)",
    }, values
    agent_c = GAZE.split("**Agent C — PR review**", 1)[1].split(
        "Wait for all spawned agents", 1
    )[0]
    assert "skip" not in agent_c.lower()
