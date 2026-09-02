---
name: feedback_guard_budget_is_net_negative
description: "Guard count only goes down — a new guard costs two retirements, and a guard that never fired beyond its own original bug is retirable"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ee1959c2-1d77-4da5-b7f5-45540c034f1b
  modified: 2026-09-02T15:22:49.595Z
---

The author, 2026-09-02, interrupting a proposal to add a seventh guard to
`make check` in search-works-for-zotero: "We have more than enough guards.
Adding one only if we remove two. Guards that never fired beyond their own
original bug can go."

**Why:** guard code is not free. `bench/check_figures.py` alone is 1 141
lines, a third of all guard code in that repo, and every guard is prose an
agent reads, a failure mode to debug, and a thing that outlives the defect it
was written for. Five guards were already retired there on 2026-09-01 on a
record of zero catches, and their rules still bind — kept by the reader
instead. The repo's own instructions say the same in the small: prefer
deleting a guard over growing it.

**How to apply:** never propose a guard as a standalone addition. Price it
first — name the two you would retire, with evidence for each that it never
caught anything beyond the bug it was born from. If you cannot name two, the
guard does not land, and the honest report is that the hazard stays unguarded
and a reader carries it. A duplication the author has deliberately ratified
(see [[feedback_verify_the_load_bearing_claim]]) does not automatically earn
mechanical enforcement.

Establishing a catch record is the work, not an aside: a guard's own
introduction commit and its immediate fixups do not count as catches. Look
for later commits that the guard forced.

Related: [[feedback_guard_the_silent_failure_first]],
[[feedback_the_tickets_own_test_needs_a_control]].
