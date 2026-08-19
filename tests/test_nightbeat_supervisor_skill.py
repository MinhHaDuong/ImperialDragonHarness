"""Adherence tests for nightbeat-supervisor — the invariants, not the prose.

This file used to assert that particular procedural sentences appeared in
SKILL.md (a literal `git status --porcelain` snippet, the sentence "Commit
tracked writes immediately", a settings.json write-point marker). Those tests
pinned an implementation into a prompt: they passed whether or not the
property held at runtime, and they blocked any rewrite of the procedure even
when the property was already enforced elsewhere in code.

Commit discipline is enforced twice already, by code: the pre-commit hook
refuses commits on the default branch, and the next cycle's dirty-tree
pre-flight aborts with `outcome=aborted-dirty-tree`. What remains here are
the properties that must survive any rewrite of the skill.
"""

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "nightbeat-supervisor"
    / "SKILL.md"
)
GOAL_CONDITION = SKILL.parent / "goal-condition.txt"

# Claude Code's /goal command rejects a longer condition (binary 2.1.232).
GOAL_CONDITION_MAX_CHARS = 4000


def _read_skill() -> str:
    return SKILL.read_text()


def _invariants_section(text: str) -> str:
    """The Invariants block, located by heading role rather than exact wording.

    The old test hard-matched "## Invariants (the only prescriptions)" and the
    following "## Executor's latitude", so renaming either heading failed the
    build for a document that still held the invariant. Match the heading that
    starts with Invariants, and end at whatever heading comes next.
    """
    match = re.search(r"^##\s+Invariants\b.*$", text, re.MULTILINE)
    assert match, "no Invariants section heading"
    rest = text[match.end() :]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    return " ".join((rest[: nxt.start()] if nxt else rest).split())


def test_self_modification_guard_is_an_invariant():
    """The read-only-own-definitions guard must be binding, not advisory.

    It belongs inside the Invariants section, so an executor cannot edit skill
    definition files mid-run while remaining formally compliant.
    """
    invariants = _invariants_section(_read_skill()).lower()
    assert "skill definition" in invariants, (
        "self-modification guard not inside the Invariants section"
    )
    assert "read-only" in invariants


def test_independent_verification_is_an_invariant():
    """Integration without an independent pass is the failure the whole run
    exists to prevent, so it must be an invariant rather than latitude.

    /goal cannot carry this one: its condition is judged by a prompt hook —
    the model assessing its own work — which is precisely the producer
    re-reading itself that the invariant forbids.
    """
    invariants = _invariants_section(_read_skill()).lower()
    assert "verification" in invariants or "verified" in invariants, (
        "no verification invariant"
    )
    assert "independent" in invariants, (
        "verification invariant does not require independence"
    )


def test_goal_condition_fits_the_command_cap():
    """The condition must fit what /goal accepts, or the run silently loses
    its stop gate at launch."""
    assert GOAL_CONDITION.exists(), "goal-condition.txt missing"
    text = GOAL_CONDITION.read_text()
    assert text.strip(), "goal condition is empty"
    assert len(text) <= GOAL_CONDITION_MAX_CHARS, (
        f"goal condition is {len(text)} chars, over the "
        f"{GOAL_CONDITION_MAX_CHARS}-char cap /goal enforces"
    )
