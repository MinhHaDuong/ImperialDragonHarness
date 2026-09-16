---
name: feedback_rebase_contaminates_from_local_main
description: git rebase onto origin/main can pull in local-only commits if local main has unpushed work
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 76fda995-7a90-4d73-8bd9-1acc840f289f
---

`git rebase origin/main` only protects against commits already on the remote. If the local `main` branch has commits that haven't been pushed (e.g. from a parallel nightbeat or agent run), those can silently contaminate the rebased branch.

**Why:** Surfaced when `773257c doc(0201)` (a user's unpushed local commit) appeared on branch `close-0187-misfiled` after rebasing. CI caught it via `erg check` duplicate-ID error.

**How to apply:** Always rebase against `origin/main` explicitly (not bare `main`). If a branch picks up unexpected commits, inspect with `git log origin/main..HEAD` before pushing. The clean fix is: create a fresh branch from `origin/main` and cherry-pick only the intended commits.
