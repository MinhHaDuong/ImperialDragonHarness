---
name: lair
description: End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session.
disable-model-invocation: false
user-invocable: true
---

# Lair — end-of-day wrap-up

Run when the user ends a work session ("done for today", "let's stop", "wrap up").

## Steps

0. **Skip-housework check**: if `$(git rev-parse --git-common-dir)/roar-last-sha` exists and `git log $(cat $(git rev-parse --git-common-dir)/roar-last-sha)..HEAD --oneline` is empty, skip steps 1–2 and 11 (nothing new since last roar).

1. **Housekeeping** — run `/molt` (git sync, healthcheck, eager fix-now repairs, ticket creation).
2. **Reflect on the session** — summarize work done. `git log --since="6am" --oneline` as starting point.
3. **Log session metrics** — run `~/.claude/skills/lair/log-agent-metrics` with: `<session_id> session <total_tokens> <tool_uses> <duration_ms> <model> <project>`. Estimate tokens from conversation length if exact count unavailable.
4. **Push all branches** — no local-only work overnight. `git branch` → ensure each non-main branch is pushed to origin.
5. **Commit WIP if needed** — uncommitted work gets `wip:` prefix, committed to the current branch, and pushed.
6. **Handoff notes** — for in-progress tickets with unpushed context, add a comment to the ticket: what's done, what's next, blockers.
7. **Exit worktree** — if in a worktree:
    a. Preflight from inside the worktree: `~/.claude/scripts/worktree-exit-preflight.sh` (refuses on any uncommitted/untracked state; closes the ExitWorktree gap, ticket 0174). If it blocks, finish step 5/6 (commit WIP, handoff notes) and re-run.
    b. Call `ExitWorktree` to return to the main working tree. All remaining steps run on main.
8. **Hygiene sweep**:
   - **GC stale worktrees** — this is the ONLY place worktree GC runs; roar and molt touch nothing outside their own worktree (2026-07-13: a mid-day GC from roar removed worktrees that were live sessions' base cwds, stranding them in unregistered husk dirs where git resolves to the primary checkout). Even here, first confirm no other Claude session is still running on this repo; if one is, skip the GC and say so. The `[gone]` status only registers after the remote-tracking ref is pruned, so fetch first:
     ```bash
     git fetch --prune origin
     ~/.claude/scripts/worktree-gc.sh
     ```
     Removes only registered worktrees on an upstream-gone branch with no uncommitted changes (and never the one it runs from); never `rm -rf`s; silent when there is nothing to remove. It also **reports (never removes) "husk" dirs** under `.claude/worktrees/` — informational, tracked by tickets 0325/0338, do NOT re-file. Follow with `git worktree prune` for leftover admin entries. See tickets 0169, 0195, 0325. Skip in a no-forge repo: without a remote, `[gone]` can never register.
   - **A worktree the GC skips for uncommitted changes is a signal, not just an obstacle**: diff it and ask "is this a closed ticket's dropped deliverable?" — `erg-pr-merge` autocloses on the `**Ticket:**` line unconditionally, so a PR can close a ticket having landed only part of the work, leaving the rest as orphaned WIP (2026-06-16: ticket 0609's mandated adherence test sat uncommitted for weeks after PR #1111 autoclosed 0609 with only the data fix). Preserve it (`wip(NNNN):` commit + push), then re-ticket and execute; never silently discard. Verify any recovered test actually runs — uncommitted WIP may never have been linted/executed.
   - `git branch -a` → delete stale remote branches
   - Check for orphan tickets and stale merge requests
9. **Full test suite** — `make check` on main. New failures → open ticket. Known failures → confirm ticket still open.
10. **Refresh STATE.md** on a throwaway branch, landed through the normal PR gate (main is branch-protected — there is no direct-push-to-main path, and STATE.md is not special-cased; rules/git.md):
    a. `git checkout -b housekeeping-state-YYYY-MM-DD main`
    b. Run `python3 "$HARNESS_DIR/scripts/refresh-STATE.py"` to regenerate `## Status` and bump `Last updated:`. Then hand-edit remaining sections (blockers, next actions, milestones) — no changelog.
    c. Prune: delete items checked off before this session.
    d. Commit, `git push -u origin housekeeping-state-YYYY-MM-DD`, open a PR (`Ticket: none`) and enable auto-merge so it lands through the gate.
    e. After the PR merges, delete the throwaway branch (local and remote).
11. **Memory consolidation** — run `/dream <project>` where `<project>` is the current project directory name. This delegates to the autonomous consolidation skill (includes staleness check, dedup, and Park reflection).
