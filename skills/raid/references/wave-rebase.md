# Raid — mid-wave rebase of the wave base

Loaded from `skills/raid/SKILL.md` § Phase 5.

**When**: origin/main advances mid-wave, after executors have already forked.

**Why**: a branch forked before or after the advance carries a different SHA of
the annotation commits, and patch-equivalent commits are not merge-equivalent —
divergent copies collide on `tickets/` at merge time.

**How**: the orchestrator first rebases WAVE_BASE itself: create a temporary
branch at OLD_WAVE_BASE and rebase it once onto the new main; its rebased tip
is NEW_WAVE_BASE. Then move each wave branch inside its executor's existing
worktree — the same worktree Phase 7 runs the recipe in. Quiesce the
executor first, then run
`git -C <worktree-path> rebase --onto NEW_WAVE_BASE OLD_WAVE_BASE` in that
worktree, where the branch is already HEAD: no `<branch>` argument and no
checkout (a `<branch>`-argument rebase from the orchestrator checkout fails
with "already used by worktree"). The rebase replays only the branch's own
commits, so the shared annotation commits replay exactly
once, never per-branch, and every branch carries the same objects. Push each
rewritten branch with `git push --force-with-lease`, explicitly authorized for
this rewrite of pushed branch SHAs. WAVE_BASE moves to NEW_WAVE_BASE.
