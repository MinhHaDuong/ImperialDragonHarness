---
name: Squash merge ticket closure timing
description: Close tickets on main after squash merge, not on the feature branch, to avoid stale-state conflicts
type: feedback
originSessionId: 18faeffc-8839-4f7e-8184-52cd59e7419b
---
Close the ticket (Status: closed) in a direct commit on main *after* the squash merge lands, not as part of the feature branch. Squash merges erase branch history, so any ticket edits on the branch end up in an older state on main (the squash commit may carry a different Status than what we set on the branch). Closing post-merge avoids the conflict entirely.

**Why:** After PR#57 squash merge, `gh pr merge` failed to fast-forward local main, leaving local main diverged with 3 extra commits. The ticket closure commit then conflicted with the squash merge's version of the ticket. Resolved via `git merge origin/main` + manual conflict resolution, but it was messy.

**How to apply:** After `gh pr merge --squash` succeeds, switch to main, pull, then commit the ticket closure separately as a clean post-merge commit.
