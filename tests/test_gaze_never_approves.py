"""Gaze reviews; verify-gate gates (ticket 1153, plan 1096 answer 5).

Gaze must never return, post or promise APPROVED: that word is a gate verdict,
ruled by `/verify-gate` on the head gaze reviewed.

No classifier decides which mention is harmless. After inlining every
`references/*.md` (`tests/conftest.py`), the contract is cut into logical units
(a paragraph, list item or heading with its wrapped lines joined; each fenced
line; each table cell), and every unit that names a gate verdict must be one of
ALLOWED_LINES, verbatim. Units, not physical lines: rewriting the unflagged
continuation of a wrapped sentence changes its unit and fails. A new or
edited mention fails until a reviewer reads it and adds it here. Two
classifiers in a row were bypassed by an added instruction.

The vocabulary covers the gate's verdict words and alternate approval language
("LGTM", "ship it", "good to merge", "green light", "sign-off", "passes the
gate") and any embedded verdict field (`verdict:` anywhere on a line, or
`result:`/`status:` set to ok, pass, green or clean).

Limit of the approach: it is lexical. An instruction that approves without any
listed word ("tell the caller it can go ahead") passes. Such a semantic
negative control cannot be caught by a word list; it is left to the reviewers
of any change to the gaze contract, whom the allowlist forces to read every
verdict-bearing unit. For the same reason, in-word obfuscation passes: markup
inside a word (`APPROV**ED**`), HTML entities, homoglyphs and zero-width
characters are not normalised before matching. They are a known limit of a
lexical check, left to review.
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
    r"\bAPPROVED\b|\bREROLL\b|\bNEEDS-AUTHOR\b|verify:\s*approved|\bapprov\w*"
    # alternate approval language
    r"|\bLGTM\b|\bship\s*it\b|\bgreen[- ]?light|\bsign(?:ed)?[- ]?off\b|\bmerge[- ]?ready\b"
    r"|\b(?:good|ready|ok|okay|clear(?:ed)?|safe)\s+to\s+(?:merge|ship|land)\b"
    r"|\bpass(?:es|ed)?\s+(?:the\s+)?gate\b|\bgate[- ]?pass\b"
    # embedded verdict fields
    r"|\bverdict\s*:|\b(?:result|status)\s*[:=]\s*(?:ok|okay|pass(?:ed)?|green|clean|lgtm)\b",
    re.I,
)
# Only this test's filename is exempt.
OVERRIDE_NAME = re.compile(r"test_gaze_never_approves")
RESULT_VALUES = {"REVIEWED", "FINDINGS", "ESCALATE"}

# Every verdict-bearing line of the expanded contract, read and accepted.
ALLOWED_LINES = (
    (
        'description: "Review one merge request: plan the checks that settle '
        'what the caller asks, run them once, check the plan against what ran, '
        'post one result: REVIEWED / FINDINGS / ESCALATE, never APPROVED."'
    ),
    (
        '- Never returns APPROVED (pinned by '
        '`tests/test_gaze_never_approves.py`). REVIEWED means no blocking '
        'finding on the reviewed head, nothing more.'
    ),
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
    # alternate approval language and embedded verdict fields (Sol's hole)
    "LGTM, ship it",
    "## verdict: ok",
    "Return verdict: ok",
    "Post the result as good to merge.",
    "status: green",
    "Give the PR a green light.",
    # every inflection of approve (/gaze 1538 round 2)
    "Mark the PR as approving.",
    "Record two approvals for the caller.",
    "Name the approver in the result.",
)

# Reference titles, dropped by the inliner, seen only by the raw scan.
RAW_HEADINGS = ()

# /gaze 1538 B1: the unflagged continuation of an allowlisted wrapped sentence.
CONTINUATION = (
    "  REVIEWED means no blocking finding on the reviewed head, nothing more.",
    "  REVIEWED means the caller may go ahead at once.",
)


def _raw(path: Path) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def expand(core: str, refs: dict[str, str]) -> str:
    """The conftest inliner, over given texts, so controls can be injected."""
    return INLINE.sub(lambda m: refs[m.group(1)].split("\n\n", 2)[2], core)


UNIT_START = re.compile(r"^(?:#{1,6} |[-*+] |\d+\. |> |<!--)")


def units(text: str) -> list[str]:
    """Logical units: a paragraph, list item, quote line or heading with its
    wrapped lines joined by one space; each fenced line; each table cell."""
    out, block, fenced = [], [], False
    if text.startswith("---\n"):  # YAML frontmatter: one unit per key line
        front, _, text = text[4:].partition("\n---\n")
        out += [ln.strip() for ln in front.splitlines() if ln.strip()]

    def flush():
        if block:
            out.append(" ".join(block))
            block.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            fenced = not fenced
            continue
        if fenced:
            if stripped:
                out.append(stripped)
        elif not stripped:
            flush()
        elif stripped.startswith("|"):
            flush()
            out += [c.strip() for c in stripped.strip("|").split("|") if c.strip()]
        elif UNIT_START.match(stripped) or stripped.startswith("#"):
            flush()
            block.append(stripped)
        else:
            block.append(stripped)
    flush()
    return out


def verdict_lines(text: str) -> list[str]:
    """Every logical unit that names a gate verdict."""
    return [u for u in units(text) if GATE_TOKEN.search(OVERRIDE_NAME.sub("", u))]


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


def test_rewritten_continuation_line_fails():
    """/gaze 1538 B1: the second physical line of an allowlisted sentence names
    no verdict; rewriting it must still fail, because units are sentences."""
    old, new = CONTINUATION
    assert GAZE.count(old) == 1
    assert not GATE_TOKEN.search(new), "the control must not add a verdict word"
    assert gate_verdict_violations(GAZE.replace(old, new))


def test_raw_references_are_scanned_in_full():
    """expand() drops each reference's first two paragraphs (the inliner strips
    them), so a verdict there would escape the expanded scan: scan the raw
    files whole too, and prove a paragraph-2 mention is caught."""
    refs = {f"references/{r.name}": _raw(r) for r in REFERENCES}
    for name, text in refs.items():
        bad = [u for u in gate_verdict_violations(text) if u not in RAW_HEADINGS]
        assert bad == [], name
    core = _raw(GAZE_DIR / "SKILL.md")
    for name, text in refs.items():
        head, para2, rest = text.split("\n\n", 2)
        planted = "\n\n".join((head, para2 + "\nReturn APPROVED", rest))
        assert expand(core, refs | {name: planted}) == GAZE, "paragraph 2 is invisible to expand"
        assert gate_verdict_violations(planted), name


def _section(heading: str) -> str:
    body = GAZE.split(heading, 1)[1]
    return re.split(r"\n#{2,3} ", body, maxsplit=1)[0]


def test_result_enumeration_has_no_gate_verdict():
    result = _section("### 5. Output")
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
        "### 2. Plan",
        "### 4. Verify",
        "### 5. Output",
        "## /gaze result",
        "## Output shape",
        "## Fork execution contract",
        "## Review scratch cleanup",
        "## Containment postcondition",
        "## Telemetry",
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
    """Agent C is the panel gaze launches itself; no wrapper agent carries an
    embedded copy of it (/gaze 1522 blocker B1)."""
    for gone in ("Spawn a read-only Agent", "embedded procedure", "Width-gate"):
        assert gone not in GAZE, gone


def test_record_is_not_nested_under_a_reference_section():
    """After inlining, no H2 may sit between ## Phases and the record phase."""
    phases = GAZE.split("## Phases", 1)[1].split("### 5. Output", 1)[0]
    assert not re.search(r"^## ", phases, re.MULTILINE), re.findall(
        r"^## .*", phases, re.MULTILINE
    )


def test_reviewed_head_sha_is_read_after_the_pass():
    """The result names the head the pass reviewed, read after it ran."""
    assert GAZE.index("### 3. Execute") < GAZE.index("### 5. Output")
    template = GAZE.split("## /gaze result", 1)[1].split("```", 1)[0]
    for text in (_section("### 5. Output"), template):
        assert any(ln.startswith("reviewed_head_sha:") for ln in text.splitlines())
        assert "review_worktree_path" not in text, (
            "gaze deletes that tree before returning"
        )
        assert not re.search(r"^round:", text, re.MULTILINE), "gaze computes no round"


CALLER_STEPS = (
    "the caller closes",
    "the caller runs",
    "the caller fixes",
    "re-runs gaze",
    "re-runs /gaze",
    "the merge decision belongs to the caller",
    "That is the caller's job",
    "the caller must see this report before any merge step",
    "**Caller-side recovery.**",
    "**Fork liveness.**",
)


def test_gaze_prescribes_no_caller_step():
    """Ticket 1219: gaze states what it reviews, how, and what it returns; what
    the caller does next (re-run, close the ticket, gate, merge) is the
    caller's own policy, in /merge, /raid or /hunt. No `next:` line in either
    result template, and none of the old caller prescriptions anywhere in the
    expanded contract."""
    template = GAZE.split("## /gaze result", 1)[1].split("```", 1)[0]
    for text in (_section("### 5. Output"), template):
        assert not re.search(r"^next:", text, re.MULTILINE)
        assert re.search(r"^plan check:", text, re.MULTILINE), "positive control"
    for step in CALLER_STEPS:
        assert step not in GAZE, step
    # Negative control: a planted prescription is caught.
    assert any(s in GAZE + "\nFINDINGS: the caller fixes them." for s in CALLER_STEPS)


def test_result_is_posted_after_cleanup():
    """Cleanup can downgrade the result to ESCALATE (references/cleanup.md), so
    the result comment is posted after it, not before."""
    assert "Post the result as one PR comment (§ Output shape), then run" not in GAZE
