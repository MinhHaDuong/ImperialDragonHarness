---
name: feedback_verify_pushes_fixes
description: "/verify can apply and PUSH fixes to the PR branch from its own review worktree, leaving your local branch stale"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 211826a9-1beb-4f8d-9a7a-952c56d075ef
---

When /verify (verify-gate) finds blocking issues, it may apply the fix
itself and push a commit to `origin/<branch>` from its isolated review
worktree (seen on PR #243: it pushed `fix(0208): byte-stable install
reruns` directly). Your local worktree branch then sits BEHIND origin.

**Why:** the skill's fix path runs in `/tmp/review-<pr>`, commits, and
pushes so the round-2 gate re-verifies from a clean origin extraction.

**How to apply:** after /verify returns APPROVED, before merging, run
`git fetch origin` and fast-forward your local branch:
`git merge --ff-only origin/<branch>`. Do NOT `git reset --hard` (a
PreToolUse guard blocks it; and it's unnecessary when you have no
uncommitted work). Then merge. If you skip the sync, a later rebase/
force-push from the stale local branch would DROP the verify fix.
Related: [[feedback_merge_ci_wait_retry]], [[feedback_simplify_commit_not_pushed]].
