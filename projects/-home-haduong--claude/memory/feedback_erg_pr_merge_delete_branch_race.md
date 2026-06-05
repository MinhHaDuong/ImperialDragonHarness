---
name: feedback-erg-pr-merge-delete-branch-race
description: "erg-pr-merge exits 1 after merge when GitHub's deleteBranchOnMerge races the local --delete-branch cleanup"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3e1255e4-ffec-4ef7-9b73-843c94d4d4d7
---

`erg-pr-merge` can exit 1 with HTTP 404 even after a successful squash-merge when run from the primary repo (not a worktree). GitHub's `deleteBranchOnMerge: true` deletes the remote branch server-side before `gh pr merge --delete-branch` can clean it up locally.

**Why:** Seen on PR #210 (t166) merge — merge succeeded, local main fast-forwarded correctly, but script exited 1. The merge is durable; the error is benign. Ticket 0170 fixed the worktree variant (main-lock error); the race-condition variant on the non-worktree path is a separate, lower-priority issue.

**How to apply:** If `erg-pr-merge` exits 1 after printing "Merging PR #N..." and the local main fast-forwarded, check `gh pr view N --json state` — if MERGED, treat as success. A follow-up ticket could make `--delete-branch` also conditional on whether the remote branch still exists.
