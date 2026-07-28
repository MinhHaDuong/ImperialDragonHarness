"""A `Label: needs-human` ticket is screened out before any executor is spawned.

Ticket 0390 (sibling of 0378). Hunt step 2b triages a ticket before code is
written, but 0378's Verification bullet 3 scopes that triage to skip for an
already-detached executor. A raid picks its own tickets and spawns its own
Phase 5 executors, so no interactive hunt ever runs the triage for them —
leaving the autonomous path, where the author is not watching, unscreened.

Two selection surfaces must therefore name the screen:

- `pick-ticket` step 1 is *already* screened, mechanically: every label in
  `tickets/.ergrc` suppresses a ticket from `erg ready` output. The fix there
  is to name that existing mechanism where a reader looks for it — NOT to add
  a second, hand-rolled label grep beside the tool-level filter that already
  does the job.
- `raid` Phase 1 reads open tickets from `tickets/` directly, never through
  `erg ready`. It must state the exclusion itself.

Every assertion is scoped to the selection region of its file. A file-wide
substring check would pass on a screen that landed in the wrong phase, which is
the tautological-test antipattern. Bounded extraction mirrors
`tests/test_hunt_triage_prestep.py`.

Text-grep hygiene test — fast tier, no marker.
"""

import functools
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PICK_TICKET = REPO / "skills" / "pick-ticket" / "SKILL.md"
RAID = REPO / "skills" / "raid" / "SKILL.md"


def _collapse(text: str) -> str:
    """Collapse whitespace so phrase assertions survive prose re-wrapping."""
    return re.sub(r"\s+", " ", text)


@functools.cache
def pick_candidates_text() -> str:
    """Return pick-ticket's step 1 (candidate selection), whitespace-collapsed.

    The lookahead anchors the region on step 2, so a screen mentioned in the
    beat-skip step or in the ranking step fails here rather than passing on a
    file-wide match.
    """
    text = PICK_TICKET.read_text()
    m = re.search(
        r"^1\. \*\*Get candidates.*?(?=^2\. \*\*Apply beat-skip)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert m, (
        "could not locate pick-ticket step 1 (Get candidates) between step 0 "
        "and step 2 (ticket 0390)"
    )
    return _collapse(m.group(0))


@functools.cache
def raid_wrapup_text() -> str:
    """Return raid's Wrap up section, whitespace-collapsed."""
    text = RAID.read_text()
    m = re.search(
        r"^## Wrap up.*?(?=^## Circuit breakers)", text, re.MULTILINE | re.DOTALL
    )
    assert m, "could not locate raid's Wrap up section (ticket 0390)"
    return _collapse(m.group(0))


@functools.cache
def raid_phase1_text() -> str:
    """Return raid Phase 1 (Select), whitespace-collapsed.

    Anchored on the Phase 2 heading: an exclusion stated in Phase 5 (Execute)
    is too late — the executor has already been spawned by then.
    """
    text = RAID.read_text()
    m = re.search(
        r"^## Phase 1: Select.*?(?=^## Phase 2:)", text, re.MULTILINE | re.DOTALL
    )
    assert m, "could not locate raid Phase 1 between its heading and Phase 2 (ticket 0390)"
    return _collapse(m.group(0))


def test_pick_ticket_names_the_skip_label_screen():
    """The screen must be visible where a reader looks for the selection rule."""
    region = pick_candidates_text()
    assert "needs-human" in region, (
        "pick-ticket's candidate-selection step must name `needs-human` as an "
        "exclusion — the screen exists (via .ergrc) but is invisible to a "
        "reader of the selection prose (ticket 0390)"
    )
    assert ".ergrc" in region, (
        "pick-ticket must name `tickets/.ergrc` as the source of the skip-label "
        "set, so a reader can see WHERE the exclusion is configured rather than "
        "trusting an unattributed claim"
    )
    assert "erg ready" in region, (
        "pick-ticket must attribute the screen to `erg ready`'s own filter — "
        "naming the label without naming the tool that applies it invites a "
        "second, hand-rolled implementation"
    )


def test_pick_ticket_does_not_hand_roll_the_screen():
    """Negative guard: one screen, applied by the tool that owns it.

    A second label filter beside `erg ready`'s would be a duplicate definition
    to keep in sync with `tickets/.ergrc`, and the drifted copy is the one that
    runs. Ticket 0390 Action 1 is explicit: name the existing mechanism, do not
    add a grep.
    """
    region = pick_candidates_text()
    # Polarity first. A pure absence check passes on any paraphrase that never
    # uses the forbidden words ("drop candidates flagged needs-human"), which
    # review round 2 demonstrated with a working mutation. Requiring the
    # delegation to be *stated* means a hand-rolled screen has to contradict a
    # sentence that is still on the page, which a reader and a diff both catch.
    assert "Rely on that filter" in region, (
        "pick-ticket's candidate-selection step must state the delegation "
        "positively — that `erg ready`'s filter IS the screen — not merely "
        "avoid the words a duplicate screen would use (ticket 0390 Action 1)"
    )
    assert "do not add a second" in region, (
        "pick-ticket must forbid a second screen in so many words; the "
        "prohibition is the part a later editor needs to see before adding one"
    )
    # Then the absence checks, with two narrowings learned from false positives.
    # Word boundaries: a bare `rg ` substring also occurs inside `erg ready`,
    # the very filter this guard exists to preserve. A following flag or quote:
    # `grep` and `jq` are also ordinary nouns in prose ("a grep, not a judgment
    # call"), and only the command-shaped use is the antipattern.
    tool = re.search(r"\b(grep|rg|awk|sed|jq)\b(?=\s*[-\"'`])", region)
    assert tool is None, (
        "pick-ticket's candidate-selection step must not hand-roll a label "
        f"screen ({tool.group(0) if tool else ''!r}) beside `erg ready`'s "
        "existing .ergrc skip-label filter (ticket 0390 Action 1)"
    )
    for phrase in ("Label:", "label header", "read the label"):
        assert phrase not in region, (
            "pick-ticket's candidate-selection step must not describe reading "
            f"the ticket's label itself ({phrase!r}) — the screen belongs to "
            "`erg ready`, which owns the .ergrc vocabulary (ticket 0390)"
        )


def test_raid_phase1_excludes_needs_human():
    """Raid reads tickets/ directly, so it must state the exclusion itself."""
    region = raid_phase1_text()
    assert "Label: needs-human" in region, (
        "raid Phase 1 must name the tell as the ticket header "
        "`Label: needs-human`, so the check is a grep and not a judgment call "
        "(ticket 0390)"
    )
    assert "never a raid target" in region, (
        "raid Phase 1 must state outright that such a ticket is NEVER a raid "
        "target — a hedge ('prefer to skip') leaves the executor spawned, "
        "which is the exact 0334/0338 failure"
    )


def test_raid_phase1_excludes_every_ergrc_label():
    """The exclusion is the label *set*, not one hardcoded member.

    `tickets/.ergrc` skip-lists `deferred` alongside `needs-human`, and Phase
    1's rationale — it bypasses `erg ready`, so it must state the exclusion
    itself — applies to both identically. Hardcoding one member leaves the
    other unscreened on exactly the path this ticket exists to close.
    """
    region = raid_phase1_text()
    assert ".ergrc" in region, (
        "raid Phase 1 must read its skip-label set from `tickets/.ergrc`, the "
        "file that already defines the vocabulary (ticket 0390, review round 1)"
    )
    assert "deferred" in region, (
        "raid Phase 1 must cover `deferred` too — it is skip-listed in .ergrc "
        "on the same footing as `needs-human`, and Phase 1 bypasses the filter "
        "that would have caught either"
    )


def test_raid_phase1_routes_the_excluded_ticket_to_the_author():
    """Excluded is not dropped: the ticket surfaces in raid's own artifact."""
    region = raid_phase1_text()
    assert "briefing" in region, (
        "raid Phase 1 must say where an excluded ticket goes, in raid's own "
        "vocabulary: the wrap-up *briefing* is this skill's artifact ('run "
        "report' names nothing that exists here) — not silently dropped from "
        "the queue (ticket 0390 Action 2)"
    )
    assert "success outcome" in region, (
        "raid Phase 1 must give the surfaced ticket the same standing 0378 "
        "gives a returned decision list — a success outcome; otherwise the "
        "orchestrator reads the exclusion as a failure and pushes on"
    )


def test_raid_wrapup_has_a_landing_spot_for_excluded_tickets():
    """A routing claim needs a destination that exists.

    Phase 1 promises the excluded ticket reaches the author. Wrap up is where
    the briefing is assembled, and it itemizes ESCALATED PRs explicitly; an
    exclusion with no matching slot there is a promise with no delivery.
    """
    region = raid_wrapup_text()
    assert "skip-labelled" in region, (
        "raid's Wrap up must itemize the tickets Phase 1 excluded, the way it "
        "already itemizes ESCALATED PRs — otherwise Phase 1's routing promise "
        "has no landing spot (ticket 0390, review round 1)"
    )


def test_raid_phase1_carves_out_an_explicit_author_id():
    """The unconditional exclusion must not revoke the author's force path.

    Ticket 0390's Invariants keep explicit forcing available. Phase 1 accepts
    comma-separated ticket IDs as well as "all open", so an exclusion stated
    without a carve-out silently drops a ticket the author typed by hand —
    turning a screen into a veto (red-team dissent, review round 1).
    """
    region = raid_phase1_text()
    m = re.search(r"Carve-out: an explicit `/raid <id>` (\w+)", region)
    assert m, (
        "raid Phase 1 must carry a labelled carve-out naming the explicit-ID "
        "invocation, so the exclusion cannot be read as overriding a ticket "
        "the caller named (ticket 0390 invariant: explicit forcing stays "
        "available)"
    )
    # Polarity, not word presence: review round 2 showed the old assertions
    # passed verbatim on prose stating the logical NEGATION of the invariant
    # ("an explicit `/raid <id>` is also dropped during discovery"). The verb
    # is what carries the meaning, so pin the verb.
    assert m.group(1) == "runs", (
        "the carve-out must say the explicitly named ticket RUNS; it currently "
        f"says {m.group(1)!r}, which inverts the invariant this guard exists "
        "to hold"
    )
    assert "discovery" in region, (
        "raid Phase 1 must scope the exclusion to target *discovery* — that "
        "word is what distinguishes the 'all open' sweep from a ticket named "
        "by ID, and without it the two paths are indistinguishable"
    )
    assert "beat.py" in region, (
        "the carve-out must name `beat.py` as a programmatic caller of the "
        "explicit-ID shape — reading 'explicit' as 'the author asked' is false "
        "for the only such caller that exists (review round 2)"
    )


def test_raid_phase1_needs_human_only_queue_returns_decisions():
    """Ticket 0390 Action 3, author-approved: decisions, not an empty run."""
    region = raid_phase1_text()
    assert "batched decision" in region, (
        "raid Phase 1 must record the Action 3 decision: a queue containing "
        "ONLY `needs-human` tickets returns the batched decision lists "
        "(rules/workflow.md § Autonomous Action Rules), so the author's one "
        "question round is not lost"
    )
    assert "empty-run report" in region, (
        "raid Phase 1 must state what the decision rules OUT — an empty-run "
        "report — or a later reader re-litigates Action 3 (ticket 0390, "
        "author approved 2026-07-28)"
    )
