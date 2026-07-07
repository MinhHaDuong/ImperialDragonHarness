---
name: roar
description: Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches.
disable-model-invocation: false
user-invocable: true
---

# Roar — post-task wrap-up

`[Execute → Celebrate]`

Run after the branch has been merged. Do not skip steps.

## Non-git projects

When the working directory is not a git repository (manuscripts, data
folders): skip the pre-check and steps 7-11; run steps 1-6 and 12.
Telemetry: use `"branch":"none-non-git-project"`. The step-3 sweep
records findings in the project's notes instead of erg tickets. State
explicitly which steps were skipped and why.
(Precedent: Œconomia manuscript wrap-up, 2026-07-07.)

## Pre-check

Verify the branch has been merged before proceeding:
```bash
git fetch origin && git merge-base --is-ancestor HEAD origin/main
```
If the ancestry check fails, do not stop yet: a rebase at the merge gate
(mandatory per `rules/git.md`) rewrites the SHA, so a checkout still on the
pre-rebase commit is patch-equivalent but not an ancestor. Fall back to:
```bash
git cherry origin/main HEAD <merge-base-or-branch-point>
```
A `-` prefix on every listed commit means the patches are already upstream —
treat that as merged and proceed. Only if commits show `+` (genuinely absent
from origin/main) stop and tell the user. Do not continue with roar in that case.

## Reflect and update

1. **Reflect**: what worked, what didn't, what was surprising.
2. **Log to telemetry**: pipe a JSON summary to `~/.claude/skills/roar/log-celebration`:
   ```bash
   echo '{"project":"<name>","branch":"<branch>","commits":<n>,"files_changed":<n>,"ticket":<number|null>}' | ~/.claude/skills/roar/log-celebration
   ```
   Then write the current HEAD SHA to the sentinel:
   ```bash
   git rev-parse HEAD > "$(git rev-parse --git-common-dir)/roar-last-sha"
   ```
3. **Sweep for similar patterns**: review the fix just completed. Grep/audit the codebase for the same anti-pattern in other files. File tickets for all instances found: `tickets/erg new "<title>"`, fill the body, `erg validate` it, then COMMIT it — don't skip the commit; an uncommitted draft is destroyed by step 9's worktree exit (see ticket 0174).
4. **Guard against regression**: if the sweep above was juicy — multiple instances of the same anti-pattern — the bug has a class shape. File a follow-up ticket for a standing regression test covering the class. Do not auto-write the test, do not bundle it into the fix PR. If the sweep found nothing, move on silently. /gaze is a per-PR gate; a standing test is what catches the class coming back in an unrelated future PR.
5. **Update project docs** if pipeline, data contract, or methodology changed.
6. **Save persistent memory**: durable lessons from this task. No sweep here — sweeps happen at `/lair`.

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
       Refuses (exit 1) when there are uncommitted/untracked files — including a fresh ticket draft `tickets/erg new` wrote but never committed. The `Bash(git worktree remove*)` PreToolUse matcher does NOT fire on `ExitWorktree`, so this is the only gate. If it blocks, commit (or `~/.claude/scripts/worktree-salvage.sh`) and re-run. See ticket 0174.
    b. Call `ExitWorktree` with action `remove`. When the pre-check
       (`git merge-base --is-ancestor HEAD origin/main`) has already
       passed, the worktree branch is fully merged — ExitWorktree's
       "N commits would be discarded" warning is a false alarm from a
       stale local main. But `discard_changes` does more than remove the
       worktree: ExitWorktree restores the session to the ORIGINAL
       checkout, and with `discard_changes: true` it also deletes the
       original branch — the one the primary checkout returns to. So
       BEFORE authorizing `discard_changes`, verify that ORIGINAL branch
       is pushed or merged (`git -C <primary> merge-base --is-ancestor
       <original-branch> origin/main`, or check it has an up-to-date
       upstream). If it carries unmerged commits, use `action: "keep"`
       instead (2026-06-10: discard_changes deleted
       `dream-consolidate-2026-06-09` and orphaned another session's
       unmerged commit at a detached HEAD). Recovery if the branch was
       deleted anyway: find the commit in `git reflog` (or the deletion
       message prints its sha) and re-create the branch with
       `git switch -c <branch> <sha>`.
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

Note: STATE.md is updated on main during `/lair`, not here.
