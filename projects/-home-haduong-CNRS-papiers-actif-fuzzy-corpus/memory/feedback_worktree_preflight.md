---
name: Check main for uncommitted edits before worktree work
description: Inspect main's working tree before creating a worktree — if files I will modify have unstaged edits, surface this before proceeding
type: feedback
originSessionId: 1fc9c85f-fca5-498b-afdc-e23121463aec
---
Before entering a worktree for a task that will touch known files
(e.g., `sections/*.tex`), run `git -C <main-repo-root> status` and check
whether any of the files I intend to modify are already modified on main.

**Why:** In the 2026-04-20 session, I created a worktree from HEAD without
checking main's working tree. Main had unstaged edits to the same
`formal_model_*.tex` files, made by a parallel author or bot. At merge time
this caused avoidable conflicts and required a mid-session rebase plus
force-push-permission-prompt cycle.

**How to apply:** At the start of a revision task, after reading the target
file but before committing changes in the worktree, run `git status` on the
main repo. If the target files show `M` (modified), either:
  1. Surface the uncommitted state to the user and ask whether those edits
     should be committed/stashed first, or
  2. Coordinate: the user may be running a parallel agent — confirm scope
     before editing.
