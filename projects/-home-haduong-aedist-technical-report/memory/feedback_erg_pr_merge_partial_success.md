---
name: feedback-erg-pr-merge-partial-success
description: erg-pr-merge may close ticket but fail to merge; retrying then fails because ticket is already closed
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea153b57-2f67-4fd5-80a6-62e7f8014652
---

When `erg-pr-merge` closes the ticket and pushes the close commit but then hits a merge conflict, retrying `erg-pr-merge` fails with "no ticket found for ID NNNN" because the ticket is already in `tickets/closed/`.

**Why:** The script closes the ticket and pushes before attempting the GitHub merge. On a merge conflict, the ticket state is already committed, so retry attempts to close it again.

**How to apply:** If `erg-pr-merge` fails partway through (ticket-close push succeeded, GitHub merge failed), skip `erg-pr-merge` on retry and go straight to `gh api repos/.../pulls/N/merge -X PUT -f merge_method=merge`. Verify via `gh pr view N --json state` that the PR is MERGED before stopping.
