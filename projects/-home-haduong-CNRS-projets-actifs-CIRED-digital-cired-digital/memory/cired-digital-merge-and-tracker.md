---
name: cired-digital-merge-and-tracker
description: cired.digital uses GitHub rebase-merge (squash now disabled) and GitHub Issues — not the global erg/merge-commit conventions
metadata: 
  node_type: memory
  type: project
  originSessionId: 5d9e36fb-8b06-47db-869d-f03d3d5477f5
---

The `CIRED/cired.digital` repo does NOT follow several global harness conventions:

- **Merge method is REBASE** (`gh pr merge --rebase`), as of 2026-07-09 (PR #274). The allowed-methods config CHANGED: `gh api repos/CIRED/cired.digital` now reports `allow_squash_merge: false`, `allow_merge_commit: true`, `allow_rebase_merge: true`. Yet **both squash and merge-commit fail**: `--squash` → "Squash merges are not allowed", `--merge` → "Merge commits are not allowed" (branch protection overrides the `allow_merge_commit: true` flag, as before). Only `--rebase` works. Prior to 2026-07-09 this repo was squash-only; do not trust either the old squash note or the global `rules/git.md` merge-commit note. Always probe the three methods if rebase ever bounces. CI checks (CodeQL Analyze ×3 + lint) must be green; they pass in ~1 min for docs/slides-only changes, so `--rebase --auto` merges promptly.
- **No local ticket system**: no `tickets/` dir, no `erg` binary, no `STATE.md`. Work is tracked via **GitHub Issues** (`gh issue list`), contrary to the global "GitHub Issues are for cross-repo coordination only" rule.
- **`delete_branch_on_merge` is FALSE** on this repo (true on the harness repo). The merged remote branch is NOT auto-deleted, so the global `rules/git.md` claim "All repos use deleteBranchOnMerge: true" is wrong here. After merging, delete the remote branch manually: `git push origin --delete <branch>`.
- After `gh pr merge --squash --delete-branch` from inside a worktree, gh prints `fatal: 'main' is already used by worktree …` — this is harmless (the PR merges; the error is just gh failing to check out main locally). Verify with `gh pr view <N> --json state`. Note `--delete-branch` does not delete the remote branch here (see above) — do it manually.

Related: [[cired-digital-dependabot-uvlock-drift]]
