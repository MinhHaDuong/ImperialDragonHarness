---
name: feedback-erg-pr-merge-partial-success
description: erg-pr-merge may close ticket but fail to merge; recovery is gh pr merge --auto, never a re-run
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea153b57-2f67-4fd5-80a6-62e7f8014652
---

When `erg-pr-merge` closes the ticket and pushes the close commit but then fails to merge, retrying `erg-pr-merge` fails with "no ticket found for ID NNNN" because the ticket is already in `tickets/closed/`.

**Why:** The script closes the ticket and pushes before attempting the GitHub merge. The close-commit push itself re-triggers CI and invalidates the previous green round, so the immediate queue attempt reports "not mergeable", and the watch-then-merge fallback can time out on "no checks reported" before the new CI round even registers (observed twice, raid 419-420, 2026-06-04).

**How to apply:** If `erg-pr-merge` fails after the ticket-close push succeeded, do NOT re-run it. Run `gh pr merge N --merge --auto` — auto-merge waits out the close-commit CI round and lands by itself. Verify via `gh pr view N --json state`. If mergeability is CONFLICTING (parallel work landed on main mid-flight), rebase + `--force-with-lease` first, then re-queue auto-merge; see [[feedback-erg-close-bookkeeping-conflict]] for the typical conflict shape.
