"""Lair step 11 suggests a dream, it never runs one (ticket 0910).

Step 11 counts journal experiences not yet covered by an accepted report in
``memory/dreams/`` and, at five or more, suggests ``/dream`` in the final
summary. Its negative semantics are the deliverable: no question, no waiting
for a response, no invocation, no timer — dream is a separate invocation by
the author. These tests pin those negatives against drift of the skill text,
in the pattern of ``tests/test_lair_state_via_pr.py`` (string-match ratchet
on the skill text; not a grep for the string '5').

The residue method: split the step into sentences, drop every sentence that
is itself a prohibition ("do not", "no ", "never", "omit"), and assert the
remaining instructions carry none of the forbidden behaviors. A raw
substring match would false-positive on the very prohibitions it guards.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

LAIR_SKILL = (REPO / "skills" / "lair" / "SKILL.md").read_text()

STEP_11_HEADING = "**Suggest a dream in the conclusion when relevant.**"

# A sentence carrying one of these markers is itself a prohibition
# (e.g. "No timer or automatic invocation."), not an instruction to forbid.
PROHIBITION_MARKERS = ("do not", "does not", "no ", "never", "omit")


def step_11() -> str:
    """The dream-suggestion step, up to any later numbered step."""
    step = LAIR_SKILL.split(STEP_11_HEADING, 1)[1]
    return step.split("\n12. ", 1)[0]


def instruction_residue(text: str) -> str:
    """Lowercased instructions left after prohibition sentences are dropped."""
    kept = [
        sentence
        for sentence in re.split(r"(?<=[.;])\s+", text.lower())
        if not any(marker in sentence for marker in PROHIBITION_MARKERS)
    ]
    return " ".join(kept)


def test_step_11_asks_no_question():
    assert not re.search(r"\bask\b|\bquestion", instruction_residue(step_11())), (
        "lair step 11 must not ask a question — the dream suggestion is "
        "informational, the session finishes without a response"
    )


def test_step_11_does_not_wait():
    assert not re.search(r"\bwait", instruction_residue(step_11())), (
        "lair step 11 must not wait for a reply — lair completes all its "
        "work and finishes"
    )


def test_step_11_does_not_launch_dream():
    assert not re.search(r"\blaunch|\binvok", instruction_residue(step_11())), (
        "lair step 11 must not launch or invoke dream — a separate "
        "invocation by the author is the whole point of the suggestion"
    )


def test_step_11_has_no_timer():
    residue = instruction_residue(step_11())
    assert not re.search(r"\btimer|\bsleep\b|\bcron\b|\bschedul", residue), (
        "lair step 11 must not set or schedule anything — no timer, no "
        "automatic invocation, the threshold check runs only inside a lair "
        "session"
    )


def test_step_11_counts_inline_from_report_ledgers():
    text = step_11()
    assert "blob" in text.lower(), (
        "lair step 11 must define the experience count inline, on the "
        "journal git blob ids compared against the accepted reports' "
        "ledgers — the data already lives in the reports"
    )
    assert "ledger" in text.lower()
    residue = instruction_residue(text)
    assert "scripts/" not in residue, (
        "the counting method must stay inline in the skill — no counting "
        "script or library (ticket 0910 antipattern)"
    )
    assert "config" not in residue, (
        "the threshold stays hardcoded in the skill text — no "
        "configuration knob (ticket 0910 antipattern)"
    )
