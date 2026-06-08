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

**Stale-ref bites branch cleanup too (2026-06-08, roar after PR #786).** Even a `git fetch --prune origin` can leave `origin/main` at the pre-merge SHA if the auto-merge lands around the same time — the prune fetch raced the merge commit. The consequence during cleanup: `git merge-base --is-ancestor <branch> origin/main` returned a FALSE "not merged" (exit 1) for a branch whose PR had already merged, so `git branch -d` refused it. Do NOT escalate to `git branch -D` on that verdict. Instead: (1) verify the merge via `gh pr view N --json state,headRefOid` (the headRefOid will equal the local branch SHA), (2) `git fetch origin main` explicitly to advance the ref, (3) re-run `--is-ancestor` — it now passes and plain `-d` works. The git.md rule "never `-D` a branch whose PR you haven't verified merged" exists precisely because this probe gives false negatives on a stale ref.
