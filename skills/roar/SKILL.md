---
name: roar
description: "Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches."
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
   **First roar in a repo: prefer a session base over the aggregate.** The
   sentinel is absent exactly once per repo, and the aggregate then collapses
   the whole session into one record — which is the loss ticket 0331 exists to
   prevent, at its worst in a batched session that merged many PRs. When the
   session's base commit is known (`origin/main` as it stood before the first
   merge, recoverable from the reflog or from the first PR's base), run the
   block above with that sha substituted for `$(cat "$SENTINEL")` in the
   `enumerate-merges.py` call, instead of falling through. Written out, that
   call is `enumerate-merges.py <session-base-sha> --until "$UNTIL" --project
   "<name>"`. It stays prose rather than a second `bash` fence on purpose:
   step 2 must offer the agent exactly ONE runnable snippet, and
   `tests/test_roar_step2_attribution.py` executes that snippet to prove the
   per-merge-request attribution invariant. A second fenced block would make
   the test's extraction ambiguous, and a test that cannot say which block it
   ran proves nothing about the one the agent runs.
   Attribution is per-PR either way; the sentinel only answers *where to start*.
   Fall back to the aggregate when no defensible base exists — rewritten
   history, squash-merges, a no-forge repo with no merge commits. (Precedent:
   padme 2026-08-21, first roar after ten merged PRs.)

   The sentinel is written from `$UNTIL` inside the block above, never from
   `HEAD`: a branch worktree's `HEAD` sits below the merge just celebrated, so
   a `HEAD` sentinel would leave that merge to be re-enumerated next time.

   A fallback line naming `FAILED` is a defect report, not a note: per-merge-request
   attribution was lost for that interval. Say so in the roar summary.
3. **Sweep for similar patterns**: review the fix just completed. Grep/audit the codebase for the same anti-pattern in other files. File tickets for all instances found: `tickets/erg new "<title>"`, fill the body, `erg validate` it, then COMMIT it — don't skip the commit; an uncommitted draft is destroyed by step 9's worktree exit (see ticket 0174). Apply the severity floor (`rules/workflow.md` § Autonomous action), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.
4. **Guard against regression**: if the sweep above was juicy — multiple instances of the same anti-pattern — the bug has a class shape. File a follow-up ticket for a standing regression test covering the class. Do not auto-write the test, do not bundle it into the fix PR. If the sweep found nothing, move on silently. /gaze is a per-PR gate; a standing test is what catches the class coming back in an unrelated future PR.
5. **Update project docs** if pipeline, data contract, or methodology changed.
6. **Save persistent memory**: durable lessons from this task. No sweep here — sweeps happen at `/lair`.

   **In a worktree session, this write is refused — defer it until after step 9.** The `projects/*/memory/**` carve-out is documented, and the harness's own path guard does exempt it, but a separate platform-native Edit/Write guard tied to the session's tracked worktree also fires and has no memory exemption (`rules/workflow.md` § Worktree paths). Reflect and decide *what* to save here; perform the write once step 9 has returned the session to the primary checkout. The failure is silent in the losing direction: a denied write reads like "memory is unavailable in this context", the natural response is to put the lesson in the final message instead, and after step 9 removes the worktree nothing distinguishes a lost lesson from a session that had none (ticket 0880, observed 2026-09-08 — three entries survived only because the write was retried after the exit, which nothing had asked for).

   **In a BACKGROUND session, step 9 does not unblock it either — use a fresh
   worktree and its own PR.** You do not need to know your own mode to apply
   this: the discriminator is the refusal itself. If the post-step-9 write into
   the primary checkout is denied for *isolation* rather than for the worktree
   path, you are in this case. Leaving the worktree returns the session to the
   shared checkout, where a second guard (background-job isolation) refuses the
   very write this step just deferred, with its own unrelated message: "this
   background session hasn't isolated its changes yet". Following the paragraph
   above therefore reproduces the loss it exists to prevent. The working path is
   `EnterWorktree` on a new name, write the memory there, commit, push, open and
   merge a memory-only PR. Interactive sessions are unaffected and keep using
   the deferral above. (Observed 2026-09-10, this repo, on a /roar that had just
   merged its own PR.)

## Close and clean up

7. **Close** the ticket if still open, then **check that the close claims of
   every recently merged PR actually ran** — not only this session's:

   ```bash
   ~/.claude/skills/roar/check-close-claims.sh --days 7 || true
   ```

   A PR body's `**Ticket:**` line is executed by `erg-pr-merge`, not by the
   forge. Any other route — a bare forge-CLI merge, the forge's web UI, another
   machine, another session — lands the code and drops the claim with no
   output, and `erg check` passes either way (git-erg PR #334, 2026-09-10:
   ticket 0276's fix sat on main while 0276 stayed open, found by luck in a
   `/perch` pass and repaired by a second PR).

   `/healthcheck` step 9 does not cover this. It reports tickets carrying a
   `Closed:` header that were never archived, so it indexes on the header being
   *present* — blind by construction to a ticket that was never closed at all.
   This script joins from the other side, merged PRs that claimed a close.

   Findings are `DROPPED` (ticket exists, no `Closed:` header) or `UNRESOLVED`
   (no such ticket here — renumbered, or this checkout is behind). Repair a
   `DROPPED` with `tickets/erg close <id>` plus `tickets/erg archive`, committed
   like any other change. Exit 2 means the forge could not be read, which is
   not an all-clear; the trailing count line says what was actually examined.
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
10. **Verify hygiene** — and run the branch sweep, which is this step's job.
    Delete only after the ancestry probe: a plain delete has no merged-check
    of its own, and a remote branch can be the only copy of an unmerged
    colleague's work.

    ```bash
    git fetch --prune
    cur=$(git branch --show-current)
    # every branch checked out in ANY worktree — a parallel session may be standing on one
    checked=$(git worktree list --porcelain | awk '/^branch /{sub("refs/heads/","",$2); print $2}')
    for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
      [ "$b" = main ] && continue     # main is always an ancestor; nothing protects it when HEAD is detached
      [ "$b" = "$cur" ] && continue   # never delete the branch you are standing on
      printf '%s\n' "$checked" | grep -qx "$b" && continue   # checked out elsewhere; not yours to delete
      git merge-base --is-ancestor "$b" origin/main && git branch -D "$b"
    done
    ```

    Where the forge does not delete merged branches itself (per-repo setting —
    check it, don't assume), the remote side accumulates the same debt:

    ```bash
    git fetch --prune
    for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin/); do
      case "$ref" in origin/*) ;; *) continue ;; esac  # skips the bare `origin` symref
      b="${ref#origin/}"
      [ "$b" = main ] && continue
      [ "$b" = HEAD ] && continue
      git merge-base --is-ancestor "$ref" origin/main && git push origin --delete "$b"
    done
    ```

    Five lines are load-bearing, each for a branch someone lost: the `case`
    guard (without it the loop deletes the bare `origin` symref, fails, and
    `set -e` aborts the sweep on its first iteration while looking like it
    worked), the `main` and current-branch guards (a detached primary checkout
    lets a plain `git branch -d main` succeed), and `-D` over `-d` (`-d` checks
    merged-into-HEAD, not merged-into-`origin/main`, so it silently refuses
    branches the probe has just proven contained), and the `grep -qx` worktree
    guard (a branch another session has checked out is an ancestor of
    `origin/main` like any other; without the guard the `git branch -D` fails as
    the FINAL command of its `&&` chain, so under `set -e` it aborts the whole
    sweep and every branch after it in iteration order is never swept — git's
    refusal is a backstop, not a guard. Match on whole LINES: `git worktree
    list` emits one branch per line, and a space-delimited membership test
    silently never fires — that bug was written here on 2026-09-10 and caught
    only by reading the output, not the exit code). The loops key on exit codes,
    not parsed output, which is what keeps them correct under an output-framing
    hook. Incident detail: memory `reference_branch_cleanup_incidents`,
    ticket 0242.

    - Then: `git branch -a` → no stale remote branches; check for stale merge
      requests.
    - No-forge repo: only check that local branches are merged into the
      default branch; there are no remote branches nor merge requests, and
      every ancestry probe compares against the local default branch.
11. **Offer** to improve workflow rules if lessons were learned.

Note: STATE.md is updated on main during `/lair`, not here. Worktree GC
belongs to housekeeping (`/molt`), not here: roar exits and disposes of its
OWN merged worktree (step 9) and touches nothing outside it. A repo-wide GC
from roar removed worktrees that were live session base cwds (2026-07-13,
ticket 0355 — a merged-and-pruned branch reads `[gone]` even while sessions
still sit in the tree), stranding those sessions in unregistered husk dirs
where git silently resolves to the primary checkout.
