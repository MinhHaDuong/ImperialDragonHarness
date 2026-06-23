---
name: Don't amend commits on open PRs
description: Force-pushing amended commits makes GitHub PR diffs confusing — always use new commits instead
type: feedback
---

Don't amend commits that are already pushed to an open PR branch.
Always create a new commit instead.

**Why:** Force push rewrites history, making GitHub show the full diff from
scratch instead of an incremental change. The reviewer loses the ability to
see what changed between reviews.

**How to apply:** After pushing a branch with a PR, only add new commits.
Amend is fine for local-only commits before the first push.
