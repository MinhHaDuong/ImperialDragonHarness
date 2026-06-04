---
name: celebrate
description: Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches.
disable-model-invocation: false
user-invocable: true
---

# Celebrate — post-task wrap-up

`[Execute → Celebrate]`

Run after the branch has been merged. Do not skip steps.

## Pre-check

Verify the branch has been merged before proceeding:
```bash
git fetch origin && git merge-base --is-ancestor HEAD origin/main
```
If the current branch is not merged into origin/main, stop and tell the user. Do not continue with celebrate.

## Reflect and update

1. **Reflect**: what worked, what didn't, what was surprising.
2. **Log to telemetry**: pipe a JSON summary to `~/.claude/skills/celebrate/log-celebration`:
   ```bash
   echo '{"project":"<name>","branch":"<branch>","commits":<n>,"files_changed":<n>,"ticket":<number|null>}' | ~/.claude/skills/celebrate/log-celebration
   ```
   Then write the current HEAD SHA to the sentinel:
   ```bash
   git rev-parse HEAD > "$(git rev-parse --git-common-dir)/celebrate-last-sha"
   ```
3. **Sweep for similar patterns**: review the fix just completed. Grep/audit the codebase for the same anti-pattern in other files. File tickets for all instances found via `/ticket-new` (which commits at its step 6 — don't skip it; an uncommitted draft is destroyed by step 9's worktree exit, see ticket 0174).
4. **Guard against regression**: if the sweep above was juicy — multiple instances of the same anti-pattern — the bug has a class shape. File a follow-up ticket for a standing regression test covering the class. Do not auto-write the test, do not bundle it into the fix PR. If the sweep found nothing, move on silently. /verify is a per-PR gate; a standing test is what catches the class coming back in an unrelated future PR.
5. **Update project docs** if pipeline, data contract, or methodology changed.
6. **Save persistent memory**: durable lessons from this task. No sweep here — sweeps happen at `/end-session`.

## Close and clean up

7. **Close** the ticket if still open.
8. **Check for tracking ticket**: if the closed ticket has a parent, check whether all sibling sub-tickets are now closed.
    - All closed → integration review: re-read all child diffs, run full test suite, verify exit criteria.
    - Any open → do nothing, tracker stays open.
9. **Exit worktree** (if in one):
    a. Preflight from inside the worktree:
       ```bash
       ~/.claude/scripts/worktree-exit-preflight.sh
       ```
       Refuses (exit 1) when there are uncommitted/untracked files — including a fresh ticket draft `/ticket-new` wrote but never committed. The `Bash(git worktree remove*)` PreToolUse matcher does NOT fire on `ExitWorktree`, so this is the only gate. If it blocks, commit (or `~/.claude/scripts/worktree-salvage.sh`) and re-run. See ticket 0174.
    b. Call `ExitWorktree` with action `remove`. When the pre-check
       (`git merge-base --is-ancestor HEAD origin/main`) has already
       passed, the worktree branch is fully merged — ExitWorktree's
       "N commits would be discarded" warning is a false alarm from a
       stale local main. Authorize `discard_changes` in that case.
    Skip if not in a worktree.
10. **GC stale worktrees** (from the main repo): prune any registered worktree on an upstream-gone branch — regardless of path or name, including ones outside `.claude/worktrees/` — intact dirs that `git worktree prune` misses. The `[gone]` status only registers after the remote-tracking ref is pruned, so fetch first:
    ```bash
    git fetch --prune origin
    ~/.claude/scripts/worktree-gc.sh
    ```
    Removes only worktrees with no uncommitted changes (and never the one it runs from); never `rm -rf`s, silent when there is nothing to clean. See tickets 0169, 0195.
11. **Verify hygiene**:
    - `git branch -a` → no stale remote branches
    - Check for stale merge requests
12. **Offer** to improve workflow rules if lessons were learned.

Note: STATE.md is updated on main during `/end-session`, not here.
