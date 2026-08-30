---
name: feedback-append-only-merge-union
description: "Two branches appending to the same slot conflict by construction; resolve by keeping both and assert the union in a script, because no gate notices a lost entry"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 43bfbf20-0cb6-46b3-bcbd-d03a2e7e6911
  modified: 2026-08-29T14:13:47.707Z
---

`spec/DECISIONS.md` conflicts every time two branches ratify in parallel: every
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
ruling and there is no second copy to notice. Ticket 0300 asks for the guard;
until it lands, the script assertion is the only thing standing between a
careless merge and a permanently lost decision.

**How to apply:** on any conflict in an append-only file (the ledger, an `erg`
log), resolve by union in a script with `assert ours in result` and
`assert theirs in result`. After a clean auto-merge on a *shared* file, grep for
each sibling's markers anyway — a clean exit is not evidence the union survived
([[feedback_verify_the_load_bearing_claim]], [[feedback_guard_the_silent_failure_first]]).
