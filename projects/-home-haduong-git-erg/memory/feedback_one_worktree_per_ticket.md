---
name: feedback-one-worktree-per-ticket
description: "One worktree per ticket, one ticket per bug; never implement a second bug's fix inside the current ticket's worktree/branch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 634006e9-7829-429a-9987-b3b551d73bdb
---

One worktree per ticket. One ticket per bug. Work isolation is paramount.

When a *new* bug/idea surfaces mid-task (even a tiny, obvious one), do NOT
start implementing it in the current worktree or branch. That is drift. The
correct moves are: (1) file a proper ticket for it, (2) leave the
implementation to its own worktree/branch later (`/start-ticket N`), and
(3) keep finishing the task at hand.

**Why:** It happened (2026-05-29, during ticket 0165's CI-fix branch). A
follow-up request to fix `erg new --author` got implemented inline in 0165's
worktree — mixing two unrelated changes in one isolation boundary, violating
one-PR-one-ticket and the worktree isolation the harness enforces. The author
called it out hard ("STOP THE PRESS"). Jumping to implementation skipped the
plan/ticket step of the workflow.

**How to apply:** Surfacing a bug → write the ticket, mention it, stop. Do not
edit code for it in the current worktree. One bug == one ticket == one branch
== one worktree == one PR. If the user asks to "fix" the new thing, still
isolate it: new ticket on main, then its own worktree. Relates to
[[feedback_branch_as_claim]] (branch is the claim signal) and
[[reference_idh_tickets]].
