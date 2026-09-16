---
name: feedback_rebase_check_status_first
description: "Always check git status before rebasing — dirty state causes \"you have unstaged changes\" abort"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8c52a371-c7aa-450c-9d12-1d9615d43926
---

Always run `git status` before `git rebase origin/main`. A dirty index (modified tracked files) aborts the rebase with "you have unstaged changes." Stash first, then rebase, then pop.

**Why:** During PR 214 merge prep, the main repo had modified `tickets/0152` and untracked files. The rebase aborted, leaving a partially resolved conflict in `docs/erg-manual.md` that needed manual cleanup.

**How to apply:** Before any rebase: `git status --short` — if non-empty, `git stash` first. After rebase succeeds: `git stash pop`.
