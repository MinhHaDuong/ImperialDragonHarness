---
name: feedback-gh-pr-merge-delete-branch-worktree
description: "From a worktree, drop --delete-branch on gh pr merge; it triggers the \"'main' is already used by worktree\" error. Repo has deleteBranchOnMerge so the remote branch goes anyway."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cc76f22b-2f1b-44a8-96d3-e21287c08d82
---

`gh pr merge <N> --merge --delete-branch` run from inside a git worktree always errors with `failed to run git: fatal: 'main' is already used by worktree at <primary>`. The **server-side merge still succeeds** — the failure is only the *local* `--delete-branch` cleanup (gh tries to switch the local checkout off the branch, and `main` is held by the primary worktree).

**Why:** This burned multiple retries across PRs #452, #457, #458 in one session. The repo sets `deleteBranchOnMerge: true`, so the remote branch is deleted automatically on merge regardless.

**How to apply:** From a worktree, run `gh pr merge <N> --merge` **without** `--delete-branch`. Then verify with `gh pr view <N> --json state,mergeCommit` and realign local main with `git -C <primary-repo> reset --hard origin/main`. Same applies to `--auto`.

**Auto-merge is ENABLED repo-wide** (`allow_auto_merge: true`). Low-ceremony chore flow: branch off latest `origin/main` → push → `gh pr create` → `gh pr merge <N> --auto --merge` (no `--delete-branch`) → walk away; GitHub merges server-side when CI is green.

Related: [[feedback-merge-skill-main-lock]], [[feedback-merge-leaves-worktree-on-main]], [[project-ci-chore-bypass-workflow]].
