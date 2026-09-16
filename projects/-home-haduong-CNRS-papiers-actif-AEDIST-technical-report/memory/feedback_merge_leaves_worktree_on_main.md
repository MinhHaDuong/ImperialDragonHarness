---
name: feedback-merge-leaves-worktree-on-main
description: "After a /merge or `gh pr merge --delete-branch`, the worktree's HEAD is left on `main` (the source branch is deleted); branch BEFORE editing more or the next commit lands on local main"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f440e047-9af1-4ea7-b14e-8782336eff40
---

After `gh pr merge --delete-branch` (or the `/merge` skill), the worktree's branch is gone and `git switch` falls back to `main`. The worktree is now sitting on `main` with the latest pulled commit. Any subsequent Edit + commit lands a stray commit on local `main`, which violates the "main is read-only" rule and requires cleanup (`git branch -f main origin/main` after moving the commit to a feature branch).

**Why:** Bit me twice on 2026-05-21 in the `fig_census_direct` polish chain — once after PR #389 (caught at commit time), once after the same flow earlier. The `--no-hard` reset guard blocked the obvious cleanup path, so the recovery was `git switch -c <new-branch> && git branch -f main origin/main && git push -u origin <new-branch>`.

**How to apply:** Immediately after any `gh pr merge` or `/merge`, before the next Edit: run `git switch -c <next-feature-branch>` (or `git switch <existing-feature>`). Treat the post-merge state as "you are on main, do not edit." If you've already edited and committed, move the commit off with `git switch -c <branch>` then `git branch -f main origin/main` (the force-update on a non-checked-out branch is non-destructive).
