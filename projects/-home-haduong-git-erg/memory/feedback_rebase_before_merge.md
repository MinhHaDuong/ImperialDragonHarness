---
name: rebase-before-merge
description: Always rebase a PR branch onto current main before merging it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b2a82551-9f5a-4ca0-bf11-1cfa0119c7c0
---

Always rebase onto current `origin/main` before calling `/merge` on any PR.

**Why:** main advances during a wave (CI rebuild commits, parallel merges). Merging a stale branch can cause the "Base branch was modified" GitHub error mid-merge, requiring an extra rebase+retry cycle. Rebasing first prevents this.

**How to apply:** In the Phase 7 merge loop, for each PR:
1. `git fetch origin`
2. Rebase the PR branch onto `origin/main`
3. Push with `--force-with-lease`
4. Wait for CI to pass on the rebased push
5. Then call `/merge <pr-number>`
