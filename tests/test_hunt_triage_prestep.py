"""Hunt step 2b routes a ticket before any code is written.

Ticket 0378 (siblings 0376, 0377) — from the 2026-07-28 trace analysis of 22
climate-finance-het kills:

- An interactive `/hunt` runs *in the author's session*, so every test dump,
  diff, and review round lands in the main context: 404k output tokens and a
  68-minute post-PR tail per kill, versus 74k and 13 minutes for the same
  contract run by a detached executor (5.4x).
- Tickets whose exit criteria hinge on author judgment stall when hunted —
  both unmerged mixed kills of that week burned full execution cycles before
  surfacing questions only the author could settle.

Both collapse to one fork at hunt entry: needs-human → return a batched
decision list; otherwise → detach to one background executor, unless the
author passed the `inline` override.

Every assertion is scoped to step 2b's own text. A file-wide substring check
would pass on a 2b that landed in the wrong place or in the wrong shape, which
is the tautological-test antipattern the raid plan flagged. Bounded extraction
mirrors `test_hunt_worktree_ownership.py`.

Text-grep hygiene test — fast tier, no marker.
"""

import functools
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "hunt" / "SKILL.md"


@functools.cache
def step2b_text() -> str:
    """Return step 2b's body with whitespace collapsed to single spaces.

    Collapsing lets phrase assertions match regardless of where prose wraps
    across lines in the source. The lookahead anchors the region on step 3, so
    a 2b inserted anywhere else — or one that swallowed step 3 — fails here
    rather than passing on a file-wide match.
    """
    text = SKILL.read_text()
    m = re.search(r"^2b\.\s.*?(?=^3\.\s)", text, re.MULTILINE | re.DOTALL)
    assert m, (
        "could not locate step 2b in hunt/SKILL.md between step 2 and step 3 "
        "(ticket 0378)"
    )
    return re.sub(r"\s+", " ", m.group(0))


def test_needs_human_label_is_a_tell():
    """The mechanical router tell is the existing `needs-human` label."""
    step2b = step2b_text()
    assert "needs-human" in step2b, (
        "step 2b must name the `needs-human` label as a triage tell — it is "
        "already in the .ergrc default label set and unused as a router "
        "(ticket 0378)"
    )
    assert "Label:" in step2b, (
        "step 2b must name the tell as the ticket header `Label: needs-human`, "
        "so the check is a grep and not a judgement call"
    )


def test_decision_verb_tells_present():
    """Judgment-shaped exit criteria are recognized by their verbs."""
    step2b = step2b_text()
    verbs = [v for v in ("decide", "arbitrate", "sign-off", "choose") if v in step2b]
    assert len(verbs) >= 3, (
        "step 2b must list the decision verbs that mark an exit criterion as "
        f"author-owned (decide / arbitrate / sign-off / choose among); found {verbs}"
    )


def test_needs_human_branch_writes_no_code():
    """A hit returns decisions to the author instead of executing."""
    step2b = step2b_text()
    assert re.search(r"do not execute", step2b, re.IGNORECASE), (
        "step 2b's needs-human branch must forbid execution outright — the "
        "0334/0338 kills failed by executing first and asking later"
    )
    assert re.search(r"batched decision", step2b, re.IGNORECASE), (
        "step 2b must return a *batched* decision list (rules/workflow.md "
        "§ Autonomous Action Rules), not a sequential question round"
    )
    assert re.search(r"success outcome", step2b, re.IGNORECASE), (
        "step 2b must state that a return to the author is a success outcome, "
        "generalizing the raid drift-guard's premise-objection path — otherwise "
        "an executor reads the return as a failure and pushes on"
    )


def test_detach_launch_line_is_mechanical():
    """The detach branch states the launch concretely, contract unparaphrased."""
    step2b = step2b_text()
    assert 'Skill(skill: "hunt", args:' in step2b, (
        "step 2b must spell out the detached executor's mechanical first action "
        'as `Skill(skill: "hunt", args: "<id>")`, mirroring raid Phase 5 — a '
        "prose paraphrase of the contract is what drifted in the aedist waves"
    )
    assert 'isolation: "worktree"' in step2b, (
        "step 2b's launch line must pin worktree isolation, which is what makes "
        "the spawned agent pass step 3's ownership check"
    )
    assert "model" in step2b, (
        "step 2b's launch line must pin `model` per raid § Model policy — an "
        "unpinned launch silently inherits the session model"
    )
    assert re.search(r"\bone\b", step2b, re.IGNORECASE), (
        "step 2b must send the work to ONE executor, not a raid: a raid for a "
        "single ticket buys the orchestrator + review-panel overhead the trace "
        "analysis measured as the top cost (ticket 0378, decision recorded)"
    )


def test_inline_override_available():
    """The author can always force the old co-working behavior."""
    step2b = step2b_text()
    assert "inline" in step2b, (
        "step 2b must document the explicit `inline` argument that keeps "
        "co-working execution in the author's session (ticket 0378 invariant: "
        "the author can always force inline execution)"
    )


def test_recursion_guard_forward_references_step_3():
    """Already-detached executors skip the triage, by step 3's own predicate."""
    step2b = step2b_text()
    assert re.search(r"step 3", step2b, re.IGNORECASE), (
        "step 2b's recursion guard must forward-reference step 3's ownership "
        "check as the discriminator; without it a detached executor re-triages "
        "and spawns another executor"
    )
    assert re.search(r"skip", step2b, re.IGNORECASE), (
        "step 2b must say that an executor passing step 3's check SKIPS the "
        "triage, not merely that it 'may'"
    )


def test_recursion_guard_does_not_duplicate_the_predicate():
    """Step 3 stays the single source of truth for worktree ownership.

    Negative guard: copying the `agent-*` / `t<id>-` predicate into 2b would
    give the harness two definitions to keep in sync, and the drifted copy is
    the one that runs first.
    """
    step2b = step2b_text()
    assert "agent-*" not in step2b, (
        "step 2b must not restate step 3's `agent-*` ownership predicate — "
        "forward-reference step 3 instead (ticket 0378 invariant: worktree "
        "ownership rules in step 3 unchanged)"
    )
    assert "git status --porcelain" not in step2b, (
        "step 2b must not restate step 3's cleanliness gate; step 3 is the "
        "single source of truth for ownership"
    )


def test_triage_precedes_any_code():
    """2b sits between the exit-criteria read and the worktree step."""
    text = SKILL.read_text()
    positions = {
        label: text.index(marker)
        for label, marker in (
            ("2", "\n2. Check the **Exit criteria**"),
            ("2b", "\n2b."),
            ("3", "\n3. Enter the ticket's **own** worktree"),
        )
    }
    assert positions["2"] < positions["2b"] < positions["3"], (
        "step 2b must sit after the exit-criteria read and before the worktree "
        f"step, so triage happens before any code is written; got {positions}"
    )
