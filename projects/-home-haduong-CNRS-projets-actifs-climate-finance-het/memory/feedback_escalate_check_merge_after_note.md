---
name: feedback_escalate_check_merge_after_note
description: "after a verify-gate ESCALATE, check whether the PR merged anyway before assuming the ticket still needs work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 76f6a2bf-72fc-44c5-afaf-4d82a6350e61
---

A ticket's log can end on a round-2 verify-gate ESCALATE (e.g. "author
sign-off missing, no reviews on the PR") while the PR actually merged hours
later — the author reviewed and merged it personally, which is the sign-off,
even though no GitHub Review object exists. Ticket 0243 sat open for two days
after PR #1045 merged because nothing reconciled the ticket log against the
merge event.

**Why:** `reviews: []` on `gh pr view` only proves no formal Review object
was created; it does not prove the author never looked at the diff. A merge
by the author's own account, especially one performed after an ESCALATE note,
is itself the missing evidence — check `mergedAt`/`mergedBy` and compare the
timestamp against the escalation note before treating the gap as still open.

**How to apply:** when picking up a ticket whose last log entry is an
ESCALATE/REROLL, first run `gh pr view <N> --json state,mergedAt,mergedBy`
on any PR the ticket references. If merged, read the merged PR body for how
the gap was actually resolved (round-1 false positives often get corrected
there) before re-doing verification work. See [[project_reorg_0159_relocation]]
for the general "ticket state can drift from git reality" caution.
