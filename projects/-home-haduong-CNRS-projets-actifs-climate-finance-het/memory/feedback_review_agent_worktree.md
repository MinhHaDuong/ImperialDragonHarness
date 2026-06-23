---
name: Review agents must use PR branch worktree
description: Red team review agent produced false positives by reading main worktree instead of the PR branch
type: feedback
---

When launching review agents for a PR, explicitly instruct them to `cd` into the PR branch worktree (e.g., `t209-move-generated-tables/`) rather than the main worktree. The main worktree has pre-PR code, so agents reading from it will report "bugs" that the PR already fixes.

**Why:** In PR #211 review, the red team agent read scripts from the main worktree and flagged "scripts still write to old paths" — a false positive since the PR branch had already updated them.

**How to apply:** In review agent prompts, specify the worktree path for file reads and greps. If the worktree no longer exists (post-merge), use `gh pr diff` as the sole source of truth.
