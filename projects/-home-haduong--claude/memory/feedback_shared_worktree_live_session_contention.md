---
name: shared-worktree-live-session-contention
description: A live session can share your worktree and switch branches between your commands — verify the branch in the same compound as every commit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8ce49305-98bf-405f-af7f-6e3e79fefdeb
---

A background job's checkout can be shared by a live interactive session that
switches branches at any moment. On 2026-07-13 the `explore-session` worktree
changed branches under a background job three times: one commit landed on a
foreign branch (`t0268-state-guard`), and a recovery `git reset HEAD~1` then
uncommitted the *other session's* newer commit because HEAD had moved again
between inspection and reset.

**Why:** `git switch` mutates shared state; separate Bash calls are not
atomic, so any branch check in an earlier call is stale by the commit call.

**How to apply:** In any worktree you did not create this session (basename
not `t<id>` or `agent-*`), anchor branch state and mutation in ONE compound:
`git branch --show-current` (assert expected) `&& git commit …`. On a
misplaced commit, capture the SHA, verify by `git show --stat` whose commit
HEAD actually is before any reset, and prefer moving *your* commit out
(cherry-pick from a fresh `git worktree add`) over resetting *their* branch.
Related: [[feedback_parallel_execute_branch_contamination]],
[[feedback_verify_agents_dirty_main_repo]].
