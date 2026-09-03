---
name: feedback-append-only-merge-union
description: "Two branches appending to the same slot conflict by construction; resolve by keeping both and assert the union in a script, because no gate notices a lost entry"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 43bfbf20-0cb6-46b3-bcbd-d03a2e7e6911
  modified: 2026-09-03T05:43:39.455Z
---

`DECISIONS.md` conflicts every time two branches ratify in parallel: every
entry goes into the same slot before `## Awaiting ratification`, so the conflict
is structural, not bad luck. It happened twice in one session (2026-08-29).

The resolution is always **keep both, in landing order** — never "take theirs".
Write the resolution as a script that *asserts* both sides survive verbatim, and
assert the specific thing the change was for (e.g. `Blocked-by: 0036` must NOT
come back). Eyeballing a resolved hunk is how one side goes missing.

**Why:** measured by sabotage, deleting a whole ratified entry (881 chars)
leaves `make check` entirely green — 171 figure pairs / 0 stale, all guards, 55
tests. `check_figures.py` guards the *digits inside* an entry, nothing counts
entries. The ledger is append-only, so nothing downstream re-derives a lost
ruling and there is no second copy to notice. Ticket 0320 (renumbered from
0300) asked for the guard; the author closed it Won't do on 2026-08-30 and
reaffirmed the close on 2026-08-31 (git history holds every prior text, a
committed census is disproportionate). So the script assertion is the standing
practice, not a stopgap.

**How to apply:** on any conflict in an append-only file (the ledger, an `erg`
log), resolve by union in a script with `assert ours in result` and
`assert theirs in result`. After a clean auto-merge on a *shared* file, grep for
each sibling's markers anyway — a clean exit is not evidence the union survived
([[feedback_verify_the_load_bearing_claim]], [[feedback_guard_the_silent_failure_first]]).

Two refinements from PR 169 (2026-09-02, three sibling PRs landing the same
morning):

- **A line-level union check has a false positive: a sibling's deliberate
  rewrite.** Main showed one line of my tip "missing" after the merge; PR #173's
  own diff had removed it when it rewrote the 0573 awaiting entry. Before
  calling a loss, grep the sibling's diff (`git diff <merge>^1 <merge>`) for
  the flagged line as a `-` line. Present there means rewritten, not dropped.
- **Assert on main, not on the tip you pushed.** #173 merged between my push
  and the forge's merge of #169, and the forge auto-merged over it. The tree
  that landed is not the tree `make check` and the union script had seen.
  Detach a worktree onto `origin/main`, rerun the gate, and assert the union
  against *both* merged parents ([[feedback_green_prs_red_union]]).

**"Union" means union of intents, not always "keep both lines" — and the case
that inverts it is a header, not a log.** 2026-09-03, PR #212: ticket 0491
carried `Blocked-by: 0490` and `Blocked-by: 0496`. Main (PR #249) closed 0490
and deleted its line; my branch closed 0496 and deleted its line; git conflicted
on the two adjacent deletions. Reading "keep both, never take theirs"
mechanically would have **kept both `Blocked-by` lines** — resurrecting two
blockers that two merged commits had just retired, and re-parking the ticket.
The correct union was to apply **both deletions and keep neither line**.

The discriminator is what each side's change *asserts*, not what it looks like
in the hunk. Both sides asserted "this blocker is gone", so the union asserts
both are gone. And the assertion is checkable rather than a matter of taste:
`tickets/closed/0490-….erg` and `tickets/closed/0496-….erg` both exist in the
merged tree, so each deletion has its event on disk. Where an append-only *log*
conflicts, the events are additions and the union keeps both lines; where a
*header* conflicts, the events may be deletions and the union removes both.
Verify the event, then take the union of events.
