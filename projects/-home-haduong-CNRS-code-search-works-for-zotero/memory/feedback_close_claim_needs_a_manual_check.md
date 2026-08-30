---
name: feedback-close-claim-needs-a-manual-check
description: "erg-pr-merge cannot run when the PR branch sits in another session's worktree; merge server-side, then close the claimed tickets by hand and verify"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 43bfbf20-0cb6-46b3-bcbd-d03a2e7e6911
  modified: 2026-08-29T14:13:59.644Z
---

`erg-pr-merge` must run from the PR head branch. In this repo several PR
branches are checked out in *other* sessions' worktrees, and the worktree
isolation guard correctly refuses `git -C` into them. So in a batched merge wave
the only route is `gh pr merge <N> --merge` — which merges the code and
**silently skips the ticket close** the PR's `**Ticket:**` line claimed.

Nothing flags this. The PR shows MERGED, `erg check` passes, `make check` is
green, and the ticket just stays open in the queue.

**Why:** happened on PRs #43 (ticket 0017) and #44 (ticket 0051), 2026-08-29.
Caught only by checking by hand afterwards. A sweep over 40 merged PRs found 3
close claims and 0 unhonoured *after* the repair — run that sweep reporting
three counts (PRs seen, claims parsed, unhonoured), because zero claims parsed
means the parser broke, not that the repo is clean.

**How to apply:** after any `gh pr merge` of a PR whose body carries a
`**Ticket:**` (not `Ticket-ref:`) line, close the ticket with the manual recipe
from `tickets/AGENTS.md` — and mind its ordering trap: `git add -u tickets/`
runs **before** the `git mv` to `closed/`, or the rename carries the pre-edit
blob and drops the `Closed:` header. Two related facts: an `.erg` ticket can
carry **several** `Blocked-by:` lines, so `grep -m1` under-reports the blocked
graph; and closing a ticket with an unmet criterion is allowed (a `**Ticket:**`
line closes unconditionally) but the residue belongs in the close reason, not
quietly ticked. See [[feedback_guard_the_silent_failure_first]].
