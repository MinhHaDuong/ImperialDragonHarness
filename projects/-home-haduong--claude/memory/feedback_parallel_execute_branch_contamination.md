---
name: parallel-execute-branch-contamination
description: "Parallel isolation:worktree execute agents contaminate each other's branches when the repo has pending commits on a non-main branch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b55b6e6-f9aa-479d-8b1f-0cdf0677cc86
---

Parallel `isolation: "worktree"` execute agents branched from a dirty starting state (the raid annotation branch) rather than clean `origin/main`, causing cross-contamination. PR 153 (0133) contained all three tickets' code changes; PR 154 (0120) had extra ticket log files from sibling agents.

**Why:** Worktree isolation protects file edits but agents still share the same git branch namespace. When a pending branch exists in the repo, agents may branch from it rather than `origin/main`.

**How to apply:**
- Before launching parallel execute agents, ensure the main repo HEAD is on a clean `origin/main` (no pending annotation branches).
- Alternatively, run execute agents sequentially if branches have already been dirtied.
- After execution, always verify each PR's file list matches only its ticket's expected files before running verify.
- The fix pattern: close contaminated PRs, delete branches, re-execute sequentially from clean state.
