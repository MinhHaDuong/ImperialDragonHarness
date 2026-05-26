---
name: feedback-api-merge-fetch-after
description: "After gh api .../merge, always git fetch origin before reading git log origin/main"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b80ae846-ed78-4277-896e-c92fcf657a58
---

After merging via `gh api repos/.../pulls/N/merge`, the local `origin/main` ref is NOT updated automatically. `git log origin/main` will show stale history until an explicit `git fetch origin`.

**Why:** Discovered during raid-320-321-322 — PR #567's merge commit was invisible in `git log origin/main` immediately after the API merge, causing the local main to look 5 commits behind. A `git fetch` revealed the true state.

**How to apply:** After any `gh api .../merge` or `gh pr merge N --merge`, run `git fetch origin` before reading `git log origin/main`, checking divergence, or fast-forwarding local main.
