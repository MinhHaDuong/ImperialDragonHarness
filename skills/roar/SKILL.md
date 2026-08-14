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
folders): skip the pre-check and steps 7-10; run steps 1-6 and 11.
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

No-forge repo (`git remote get-url origin` fails — no `origin`, e.g. a
direct-to-master checkout with only ssh peers): there is no forge gate.
"Merged" means committed to the local default branch — verify with
`git merge-base --is-ancestor HEAD <master|main>` — and every `origin/main`
probe in this skill is moot. Downstream, degrade as molt/healthcheck do: a
missing prerequisite yields an explicit skip with a one-line reason, never a
fail. Concretely: step 9's ancestry checks compare against the local default
branch; step 10 reduces to checking that local branches are merged into the
default branch — there are no remote branches nor merge requests to inspect.

## Reflect and update

1. **Reflect**: what worked, what didn't, what was surprising.
2. **Log to telemetry**: log one celebration per merged PR since the sentinel,
   falling back to a single aggregate entry when no merge commits are found.
   A batched interactive session merges several PRs then roars once, so a single
   aggregate blob loses per-ticket attribution (ticket 0331). Enumerate the merge
   commits in `roar-last-sha..$UNTIL` and log each as its own record when the
   sentinel exists, is an ancestor of `$UNTIL`, and the enumeration is non-empty.
   Substitute `<name>` with the project's own directory name — the leading dash
   of a `~/.claude/projects/` slug is part of it and stays in the record:
   ```bash
   SENTINEL="$(git rev-parse --git-common-dir)/roar-last-sha"
   # Which reference to enumerate up to. /roar normally runs from the worktree
   # of the branch just merged, and that worktree sits on the branch tip —
   # BELOW the merge commit — so HEAD would miss the very merge being
   # celebrated, silently (ticket 0500). Target origin/main whenever HEAD is
   # already contained in it; HEAD is the fallback wherever no origin/main
   # exists (no-forge repo, or a differently-named default branch).
   UNTIL=HEAD
   if git rev-parse --verify --quiet origin/main >/dev/null &&
      git merge-base --is-ancestor HEAD origin/main; then
       UNTIL=origin/main
   fi
   echo "roar telemetry: enumerating up to $UNTIL ($(git rev-parse --short "$UNTIL"))"
   ROWS=""
   REASON=""
   if [ ! -f "$SENTINEL" ]; then
       REASON="no sentinel yet — first roar in this checkout"
   elif ! git merge-base --is-ancestor "$(cat "$SENTINEL")" "$UNTIL"; then
       REASON="sentinel is not an ancestor of $UNTIL — history rewritten"
   elif ! ROWS="$(~/.claude/skills/roar/enumerate-merges.py "$(cat "$SENTINEL")" --until "$UNTIL" --project "<name>")"; then
       ROWS=""
       REASON="enumeration FAILED — per-merge-request attribution lost, investigate"
   elif [ -z "$ROWS" ]; then
       REASON="no merge commits in range — squash merge, or nothing merged"
   fi
   if [ -n "$ROWS" ]; then
       # Per-PR path: one telemetry-equivalent record per merged PR.
       printf '%s\n' "$ROWS" | while IFS= read -r row; do
           printf '%s\n' "$row" | ~/.claude/skills/roar/log-celebration
       done
   else
       # Aggregate fallback — always says WHY, so a swallowed failure cannot
       # pass for a legitimate degradation (they produce the same one record).
       echo "roar telemetry: aggregate fallback — $REASON" >&2
       echo '{"project":"<name>","branch":"<branch>","commits":<n>,"files_changed":<n>,"ticket":<number|null>}' | ~/.claude/skills/roar/log-celebration
   fi
   # Sentinel = the reference just enumerated, not HEAD: a branch worktree's
   # HEAD is below it, and the next roar would re-enumerate the same merges.
   git rev-parse "$UNTIL" > "$SENTINEL"
   ```
   A fallback line naming `FAILED` is a defect report, not a note: per-merge-request
   attribution was lost for that interval. Say so in the roar summary.
3. **Sweep for similar patterns**: review the fix just completed. Grep/audit the codebase for the same anti-pattern in other files. File tickets for all instances found: `tickets/erg new "<title>"`, fill the body, `erg validate` it, then COMMIT it — don't skip the commit; an uncommitted draft is destroyed by step 9's worktree exit (see ticket 0174). Apply the severity floor (rules/workflow.md § Autonomous Action Rules), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.
4. **Guard against regression**: if the sweep above was juicy — multiple instances of the same anti-pattern — the bug has a class shape. File a follow-up ticket for a standing regression test covering the class. Do not auto-write the test, do not bundle it into the fix PR. If the sweep found nothing, move on silently. /gaze is a per-PR gate; a standing test is what catches the class coming back in an unrelated future PR.
5. **Update project docs** if pipeline, data contract, or methodology changed.
6. **Save persistent memory**: durable lessons from this task. No sweep here — sweeps happen at `/lair`.

## Close and clean up

7. **Close** the ticket if still open.
8. **Check for tracking ticket**: if the closed ticket has a parent, check whether all sibling sub-tickets are now closed.
    - All closed → integration review: re-read all child diffs, run full test suite, verify exit criteria, and run a **repo-wide union sweep for the change class** (stale refs, moved/renamed paths) — a green suite does not exercise the build graph, so a dangling build reference survives every per-PR check. It is caught only by grepping the whole tree for the class of change at integration, not per-PR. (2026-07-11, 0240 reorg: a merged `.mk` prerequisite kept a moved script's old flat path; per-move greps and green `make check-fast` all passed — only the integration union grep found it.)
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
       stale local main — it can even name a branch that no longer
       exists (a parallel session's hygiene pruned it post-merge;
       `git rev-parse --verify refs/heads/<branch>` confirms,
       climate-finance-het 2026-07-22). But `discard_changes` does more than remove the
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
    No-forge repo: every ancestry probe in this step compares against the
    local default branch instead of `origin/main`.
    Skip if not in a worktree. When roar runs inside an `isolation:"worktree"`
    subagent, `ExitWorktree` is unavailable — skip this step; the harness
    auto-cleans the agent's worktree once its branch is merged and the tree
    is clean.
10. **Verify hygiene**:
    - `git branch -a` → no stale remote branches
    - Check for stale merge requests
    - No-forge repo: only check that local branches are merged into the
      default branch; there are no remote branches nor merge requests.
11. **Offer** to improve workflow rules if lessons were learned.

Note: STATE.md is updated on main during `/lair`, not here. Worktree GC
belongs to housekeeping (`/molt`), not here: roar exits and disposes of its
OWN merged worktree (step 9) and touches nothing outside it. A repo-wide GC
from roar removed worktrees that were live session base cwds (2026-07-13,
ticket 0355 — a merged-and-pruned branch reads `[gone]` even while sessions
still sit in the tree), stranding those sessions in unregistered husk dirs
where git silently resolves to the primary checkout.
