---
name: lair
description: "End-of-day session wrap-up. Runs housekeeping, pushes branches, runs tests, refreshes STATE, offers autonomous session."
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
   - Stale worktrees were GC'd by `/molt` at step 1 (housekeeping owns worktree GC; the script's rails protect active sessions — ticket 0355). Here, just `git worktree prune` for leftover admin entries of already-deleted dirs.
   - **A worktree the GC skipped for uncommitted changes is a signal, not just an obstacle**: diff it and ask "is this a closed ticket's dropped deliverable?" — `erg-pr-merge` autocloses on the `**Ticket:**` line unconditionally, so a PR can close a ticket having landed only part of the work, leaving the rest as orphaned WIP (2026-06-16: ticket 0609's mandated adherence test sat uncommitted for weeks after PR #1111 autoclosed 0609 with only the data fix). Preserve it (`wip(NNNN):` commit + push), then re-ticket and execute; never silently discard. Verify any recovered test actually runs — uncommitted WIP may never have been linted/executed.
   - `git branch -a` → delete stale remote branches
   - Check for orphan tickets and stale merge requests
9. **Full test suite** — `make check` on main. New failures → open ticket. Known failures → confirm ticket still open.
10. **Refresh STATE.md** on a throwaway branch, landed through the normal PR gate (main is branch-protected — there is no direct-push-to-main path, and STATE.md is not special-cased; rules/git.md):
    a. `git checkout -b housekeeping-state-YYYY-MM-DD main`
    b. Run `python3 "$HARNESS_DIR/scripts/refresh-STATE.py"` to regenerate `## Status` and bump `Last updated:`. Then hand-edit remaining sections (blockers, next actions, milestones) — no changelog.
    c. Prune: delete items checked off before this session.
    d. Commit, push the branch, open a merge request (`Ticket: none`), then **land it yourself** — a STATE refresh is the agent's own output with no blast radius, and handing the author a merge to perform is what this step exists to avoid. Which mechanism lands it is a per-repo fact: **read it from the forge, never assume it.**
       - Auto-merge available and enabled on the repo → enable it on the merge request; it lands on its own once the forge's requirements are met.
       - Otherwise → fall back to the repo's own proportionality path (a "trivial review" label where one exists, plus a single review), then merge directly.

       Both halves are load-bearing. This step named auto-merge alone for months; in a consumer repo where that setting was off, a session following it literally stopped at the open merge request and handed the author the merge (2026-09-10). Whatever had landed the earlier STATE refreshes there, it was never auto-merge — and nothing in the step said to check. A step that names one mechanism without a probe assumes every repo shares one configuration, and fails silently in the direction of extra author work.
       <!-- harness-extension-point -->
       Current-generation spelling: `gh api repos/<owner>/<repo> --jq .allow_auto_merge` to read it, `gh pr merge <N> --auto --merge` to arm it.
    e. After the PR merges, delete the throwaway branch (local and remote).
11. **Memory consolidation** — run `/dream <project>` where `<project>` is the current project directory name. This delegates to the autonomous consolidation skill (includes staleness check, dedup, and Park reflection).
