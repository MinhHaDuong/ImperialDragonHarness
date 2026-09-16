---
name: feedback-rebase-large-rename
description: "When a large rename PR lands mid-wave, cherry-pick onto fresh main beats rebasing old branch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0bf1ac7d-829a-48b8-833c-94a12f02f0ab
---

When a large rename PR (like tag→label, 40+ files) lands while parallel PRs are in flight, rebasing the old branches often fails silently — the rebase appears to succeed but the branch base stays at the old commit (same tree hash, git skips the commit). The push shows "up-to-date" even though the conflict is unresolved.

**Why:** The rebase produces a commit with the same file content as the existing remote tip (because the conflict resolution and the prior fixup commit together equal the old tip), so git considers it a no-op and doesn't update the ref.

**How to apply:** When `git push --force-with-lease` says "up-to-date" after a rebase and the PR still shows CONFLICTING, abandon the rebase approach. Instead:
1. `git switch -c fresh-branch origin/main`
2. `git cherry-pick <commit1> <commit2>` — apply only the PR's meaningful commits
3. Resolve the now-small conflict (usually just the one changed line)
4. `git push origin fresh-branch:<original-branch> --force-with-lease`

This produces genuinely new commit hashes based on current main. Detected in PR #189 (0173) after 0175's tag→label rename landed.
