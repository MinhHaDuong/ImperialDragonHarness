---
name: feedback_bundle_followup_tickets
description: "raid/review follow-ups → bundle the ticket file into the spawning PR branch, not main"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1c825fe-8065-4dc5-bf57-fbc55df60426
---

When a raid/review surfaces a follow-up (a pre-existing or out-of-scope finding,
e.g. a Copilot nit), open the follow-up **ticket** via `/ticket-new` and commit
it onto the **current PR branch** — bundle it with the PR that spawned it.
Reference it from the PR body/comment. Commit the ticket only, not the fix.

**Why:** Confirmed by the author during raid 0175 (2026-05-30). Trying to land a
follow-up ticket "cleanly on main" stalls — main is often checked out and dirty
in the main repo (parallel work), so you can't commit there from a worktree.
Bundling the ticket file with its parent PR is benign (additive `.erg`, validates
clean, can't affect the code change) and keeps the finding from being lost.

**How to apply:** `/ticket-new` → commit the new `tickets/NNNN-*.erg` on the PR
branch → note it in the PR as a "Related follow-up" / "Scope overflow: tickets/NNNN"
line. The parent PR's `**Ticket:**` line still closes only its own ticket on
merge; the bundled follow-up stays open. See [[feedback_rename_hard_not_aliased]].

Author wants this convention recorded in the AGENTS instructions at raid-celebration
time (confirm which AGENTS file before editing — several exist).
