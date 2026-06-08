---
name: feedback_cross_repo_tickets_live_at_destination
description: A ticket for work in repo X must be filed in repo X's own store, not parked in the originating repo; trackers reference cross-repo work, never own foreign-repo child tickets
metadata:
  type: feedback
---

When a tracker in repo A spawns work that executes in repo B (a git-erg fix, a
cadens sweep, an other-repo residue removal), the actionable ticket belongs in
**repo B's** `tickets/` store — created from a session rooted there (or via a
forge issue for cross-repo coordination). Do NOT file a "go do X in repo B"
child ticket in repo A's store.

**Why:** tickets are local per-repo (`tickets/AGENTS.md`); a session rooted in
repo B reads `B/tickets/`, never `A/tickets/`, so a foreign-repo ticket parked
in A is invisible exactly where the doer looks — the opposite of a handoff. The
tell: if a ticket body has to say "run this from a session rooted in *another*
repo," the ticket itself is in the wrong store. Bit twice in the 2026-06-08
raid — the raid/handoff guidance had me file 0235/0236 (other-repo sweeps) and
0237/0238 (git-erg work) in IDH; the author caught it. Corrected by collapsing
A-side children into a self-contained tracker checklist and filing the real
ticket at the destination (git-erg 0242 in git-erg's store; cadens fixed via a
cadens PR).

**How to apply:** keep the originating-repo ticket as a thin tracker that holds
only the checklist + the handoff *spec* (ready to paste). The actionable ticket
is `erg new`'d at the destination when a session lands there. I CAN act on
another repo from the current session via `git -C <path>` (branch + PR there),
but the ticket still lives in that repo's store, not mine. Reserve A-side child
tickets for work that genuinely executes in A (e.g. the IDH re-vendor half of a
two-repo fix). See [[feedback_workflow_agents_session_bound]] (same session-bound
root cause), [[feedback_verify_each_before_batch_action]].
