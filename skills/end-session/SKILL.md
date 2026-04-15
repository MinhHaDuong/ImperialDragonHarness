---
name: end-session
description: End-of-day session wrap-up. Pushes branches, runs tests, refreshes STATE, offers autonomous session.
disable-model-invocation: false
user-invocable: true
---

# End session — day wrap-up

Run when the user ends a work session ("done for today", "let's stop", "wrap up").

## Steps

1. **Reflect on the session** — summarize work done. `git log --since="6am" --oneline` as starting point.
2. **Log session metrics** — run `~/.claude/skills/end-session/log-agent-metrics` with: `<session_id> session <total_tokens> <tool_uses> <duration_ms> <model> <project>`. Estimate tokens from conversation length if exact count unavailable.
3. **Push all branches** — no local-only work overnight. `git branch` → ensure each non-main branch is pushed to origin.
4. **Commit WIP if needed** — uncommitted work gets `wip:` prefix, committed to the current branch, and pushed.
5. **Handoff notes** — for in-progress tickets with unpushed context, add a comment to the ticket: what's done, what's next, blockers.
6. **Exit worktree** — if in a worktree, call `ExitWorktree` to return to the main working tree. All remaining steps run on main.
7. **Hygiene sweep**:
   - `git worktree list` → remove any stale worktrees (`git worktree prune`)
   - `git branch -a` → delete stale remote branches
   - Check for orphan tickets and stale merge requests
8. **Full test suite** — `make check` on main. New failures → open ticket. Known failures → confirm ticket still open.
9. **Refresh STATE.md** on a throwaway branch:
   a. `git checkout -b housekeeping-state-YYYY-MM-DD main`
   b. Rewrite STATE: current stats, blockers, next actions, milestones. No changelog.
   c. Prune: delete items checked off before this session.
   d. Commit, merge to main via fast-forward, delete branch.
10. **Memory sweep** — follow `/memory` skill (includes staleness check + rule cross-reference).
11. **Autonomous session** — offer to launch `/orchestrator all open` if user wants unsupervised work overnight.
