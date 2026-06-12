---
name: gh merge fails in worktree
description: gh pr merge fails with "main already used by worktree" — pass --repo flag explicitly
type: feedback
---

`gh pr merge` from inside a git worktree fails with `fatal: 'main' is already used by worktree at ...` because it tries to switch to main locally after merge.

**Why:** The worktree can't checkout main — the parent repo already has it checked out.

**How to apply:** When merging PRs from a worktree, always pass `--repo owner/repo` explicitly, e.g.:
```
gh pr merge 80 --merge --delete-branch --repo MinhHaDuong/aedist-technical-report
```
