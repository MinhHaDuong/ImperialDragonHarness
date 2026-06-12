---
name: merge-review-merge-cadence
description: "User prefers prompt merges over long-lived branches — merge as soon as approved+green, sequential rebase-merge-rebase"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6f02f069-f31e-43f6-bcdd-4f9798d60570
---

The user prefers a "merge, review, merge" cadence: land each PR as soon as it is
APPROVED and CI-green rather than letting branches live long and batch-merging.
Stated 2026-06-11 when pre-authorizing autonomous merge of the 0524 conversion
PR: "I prefer merge review merge than long-lived branches."

**Why:** Long-lived branches accrue staleness continuously under this project's
parallel-session workflow (multiple raids/hunts merging to main hourly); every
hour unmerged is rebase debt and review-verdict decay.

**How to apply:** When orchestrating multiple PRs, merge each one immediately
after its gate clears (rebase → CI → merge → next), instead of stacking
approvals and merging in a batch at the end. Pre-authorization for a specific
merge can be requested when the user steps away; once granted for a scoped
deliverable, act on it without re-asking. Related: [[gh-merge-worktree]],
rebase-at-every-gate rule in rules/git.md.
