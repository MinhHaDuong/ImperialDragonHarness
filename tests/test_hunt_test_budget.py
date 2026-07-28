"""Guard: hunt/gaze name a test-run budget; the old unbounded wording is gone.

Ticket 0376. Trace analysis (2026-07-28, climate-finance-het) measured full
`make check` re-runs as the single largest active-time bucket across 22
hunt/raid kills (27.8%): executors re-ran the full suite after single-file
edits mid-loop, and every review-fix cycle re-ran it again. Fix: `make
check-fast` (or the affected test file) is the loop gate everywhere except
the one-time full `make check` immediately before PR-open / before the fix
agent's final push.

RED proof: on the pre-fix hunt/SKILL.md, step 8 reads "implement until
`make check` passes" (no `-fast`) — this trips
test_hunt_step8_drops_unbounded_full_check_wording. The three positive-marker
tests also fail pre-fix: step 8's block carries no `check-fast` mention, the
steps 12-13 block carries neither `check-fast` nor a budget word ("once"/
"budget"), and gaze's Fix-agent contract carries none of them either.

Loose positive markers only (prose-test polarity rule): this file never
pins the new sentence verbatim. Markers are scoped to the specific step's
text block (not "anywhere in the file") so a fix that mentions check-fast
in an unrelated step does not satisfy these tests.
"""

import functools
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HUNT = REPO / "skills" / "hunt" / "SKILL.md"
GAZE = REPO / "skills" / "gaze" / "SKILL.md"

BUDGET_KEYWORDS = ("once", "budget")


@functools.cache
def _hunt_text() -> str:
    """Read hunt/SKILL.md once for the three tests that slice it."""
    return HUNT.read_text()


def _block(text: str, start_marker: str, end_marker: str) -> str:
    """Return the slice of `text` between two literal markers."""
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def test_hunt_step8_drops_unbounded_full_check_wording():
    """The old 'implement until `make check` passes' loop gate must be gone."""
    text = _hunt_text()
    assert "implement until `make check` passes" not in text, (
        "hunt step 8 still tells the executor to loop on full `make check` — "
        "the loop gate should be `make check-fast` (or the affected test "
        "file), per ticket 0376's test-run budget"
    )


def test_hunt_step8_names_check_fast_as_loop_gate():
    """Step 8's replacement wording names check-fast as the loop gate."""
    text = _hunt_text()
    block = _block(text, "8. Announce", "9. Pre-PR self-gate")
    assert "check-fast" in block, (
        "hunt step 8 must name `make check-fast` (or the affected test "
        "file) as the implementation loop gate"
    )


def test_hunt_review_fix_loop_names_a_test_budget():
    """Steps 12-13 must name check-fast and bound full-check re-runs."""
    text = _hunt_text()
    block = _block(text, "12. Fix all comments", "escalate (see workflow rules)")
    assert "check-fast" in block, (
        "hunt's review-fix loop (steps 12-13) must name `make check-fast` "
        "as the per-cycle test gate, not the full suite"
    )
    assert any(kw in block for kw in BUDGET_KEYWORDS), (
        "hunt's review-fix loop must bound full `make check` re-runs to a "
        "one-time/budgeted case, not per fix cycle"
    )


def test_gaze_fix_agent_contract_names_a_test_budget():
    """The Fix-agent contract must name check-fast and bound full-check reruns."""
    text = GAZE.read_text(encoding="utf-8")
    block = _block(text, "## Fix-agent contract", "Push commits to the PR branch")
    assert "check-fast" in block, (
        "gaze's Fix-agent contract must name `make check-fast` as the fix "
        "agent's test gate"
    )
    assert any(kw in block for kw in BUDGET_KEYWORDS), (
        "gaze's Fix-agent contract must bound full `make check` to a "
        "one-time/budgeted case before push, not per fix"
    )
