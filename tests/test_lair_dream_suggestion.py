"""Lair step 11 suggests a dream, it never runs one (ticket 0910).

Step 11 counts journal experiences not yet covered by an accepted report in
``memory/dreams/`` and, at five or more, suggests ``/dream`` in the final
summary. Its negative semantics are the deliverable: no question, no waiting
for a response, no invocation, no timer — dream is a separate invocation by
the author. These tests pin those negatives against drift of the skill text,
in the pattern of ``tests/test_lair_state_via_pr.py`` (string-match ratchet
on the skill text; not a grep for the string '5').

The residue method (hardened after the round-1 review's mutant evidence): a
prohibition is deleted only with its own scope — from the marker to the next
sentence or clause boundary — so a forbidden verb sharing a sentence with a
hedge ("Ask the user whether to run dream, no more than once.") survives the
deletion and fails the ratchet. Dropping whole sentences on a substring
marker let exactly those mutants through; the markers are word-boundary
anchored so "piano" or "know" cannot shield a sentence either.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

LAIR_SKILL = (REPO / "skills" / "lair" / "SKILL.md").read_text()

STEP_11_HEADING = "**Suggest a dream in the conclusion when relevant.**"

# A prohibition deletes only its own scope: the marker plus the text up to the
# next sentence or clause boundary (. ; :). Word boundaries keep "piano" or
# "know" from matching the "no" marker.
PROHIBITION_SCOPE = re.compile(r"\b(?:do(?:es)? not|never|omit|no)\b[^.;:]*")

# The forbidden instruction vocabulary, broadened after the round-1 mutants
# ("Run /dream now.", "Prompt the user to confirm.", "Set a reminder",
# "Run it via CronCreate." all passed the first, narrow vocabulary).
QUESTION = re.compile(r"\bask\b|\bquestion|\bprompt\b|\bconfirm\b|\banswer")
WAITING = re.compile(r"\bwait|\bpoll\b|\bblock\b|\bpause\b")
LAUNCH = re.compile(r"\blaunch|\binvok|\brun|\bstart\b|\bexecut|\bspawn")
TIMER = re.compile(r"\btimer|\bsleep\b|\bcron|\bschedul|\bremind|\balarm\b|\bwakeup")


def step_11() -> str:
    """The dream-suggestion step, up to any later step or heading."""
    step = LAIR_SKILL.split(STEP_11_HEADING, 1)[1]
    return re.split(r"\n(?=\d+\. |# )", step, 1)[0]


def instruction_residue(text: str) -> str:
    """Lowercased text with each prohibition's scope deleted from it."""
    return PROHIBITION_SCOPE.sub(" ", text.lower())


def test_step_11_asks_no_question():
    assert not QUESTION.search(instruction_residue(step_11())), (
        "lair step 11 must not ask a question or prompt for confirmation — "
        "the dream suggestion is informational, the session finishes "
        "without a response"
    )


def test_step_11_does_not_wait():
    assert not WAITING.search(instruction_residue(step_11())), (
        "lair step 11 must not wait, poll or block for a reply — lair "
        "completes all its work and finishes"
    )


def test_step_11_does_not_launch_dream():
    assert not LAUNCH.search(instruction_residue(step_11())), (
        "lair step 11 must not launch, invoke, run, start or spawn dream — "
        "a separate invocation by the author is the whole point of the "
        "suggestion"
    )


def test_step_11_has_no_timer():
    assert not TIMER.search(instruction_residue(step_11())), (
        "lair step 11 must not set or schedule anything — no timer, "
        "reminder, alarm or automatic invocation; the threshold check runs "
        "only inside a lair session"
    )


def test_step_11_keeps_threshold_and_suggestion_text():
    text = step_11()
    assert "5 or more new experiences" in text, (
        "lair step 11 must keep the hardcoded five-experience threshold in "
        "its own words — the suggestion appears only above it and the "
        "summary stays silent below"
    )
    assert "/dream <project-repository>" in text, (
        "lair step 11 must keep the suggestion's `/dream "
        "<project-repository>` quote — the author's separate invocation is "
        "the follow-up being suggested"
    )
    assert "final summary" in text, (
        "the suggestion belongs to lair's final summary — after all lair "
        "work, not mid-run"
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
