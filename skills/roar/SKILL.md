---
metadata:
  category: session
name: roar
description: "Post-task wrap-up after a merge: reflect, capture significant facts, update state, clean task branches. Not for consolidating or auditing memory (/hoard) or ending the day (/lair)."
disable-model-invocation: false
user-invocable: true
---

# Roar — post-task wrap-up

Neighbouring skills and when to prefer each: [session-lifecycle](../lair/references/session-lifecycle.md).

`[Execute → Reflect]`

Run after the branch has been merged. Do not skip steps.

The runtime gives the absolute path of the `SKILL.md` it loaded. Use that path
where the snippets say `<loaded-roar-SKILL.md>`. Resolve its directory
physically: Claude Code can load the canonical directory directly, while Codex
and Pi may load a symlink under `.agents/skills`. The resolved directory holds
roar's helpers; its grandparent is the IDH checkout. Keep the project working
directory unchanged.

## Non-git projects

When the working directory is not a git repository (manuscripts, data
folders): skip the pre-check and steps 7-10; run steps 1-6 and 11.
The step-4 sweep records findings in the project's notes instead of erg tickets. State
explicitly which steps were skipped and why.

## Pre-check

If the merge was only queued (checks were pending), ask the outcome once:

```bash
ROAR_SKILL_MD="<loaded-roar-SKILL.md>"
IDH_ROOT="$(cd -P "$(dirname "$ROAR_SKILL_MD")/../.." && pwd -P)"
"$IDH_ROOT/skills/merge/erg-pr-status" N
```

Exit 0 merged, proceed; 2 pending, wait as `skills/merge/SKILL.md` § Waiting
for a queued merge prescribes (one background command bounded at about 25
minutes, polling this status inside it), then continue this pre-check and the
cleanup yourself when it wakes you; never ask the author to wait or to re-run
`/roar`. Only a runtime that cannot wake the session when a background command
exits stops and reports the merge as pending. 1 failed, report it. Then verify the branch has been merged before proceeding:
```bash
ROAR_BASE_RC=0
git symbolic-ref -q refs/remotes/origin/main >/dev/null 2>&1 || ROAR_BASE_RC=$?
[ "$ROAR_BASE_RC" -eq 1 ] || { echo "Roar: integration ref symbolic or unreadable; keep all work" >&2; exit 2; }
git fetch --refmap= --no-prune --no-prune-tags --no-tags \
  --no-recurse-submodules --no-auto-gc --no-write-commit-graph origin \
  +refs/heads/main:refs/remotes/origin/main ||
  { echo "Roar: integration fetch failed; keep all work" >&2; exit 2; }
git merge-base --is-ancestor HEAD refs/remotes/origin/main
```
If metadata verification or fetch fails, preserve all work and report that
integration could not be verified. The fallback below applies only after a
successful fetch. If the ancestry check fails, do not stop yet: a rebase at the merge gate
(mandatory per `rules/git.md`) rewrites the SHA, so a checkout still on the
pre-rebase commit is patch-equivalent but not an ancestor. Fall back to:
```bash
git cherry refs/remotes/origin/main HEAD <merge-base-or-branch-point>
```
A `-` prefix on every listed commit means the patches are already upstream —
treat that as merged and proceed. Only if commits show `+` (genuinely absent
from refs/remotes/origin/main) stop and tell the user. Do not continue with roar in that case.

No-forge repo (`git remote get-url origin` fails — no `origin`, e.g. a
direct-to-master checkout with only ssh peers): there is no forge gate.
"Merged" means committed to the local default branch — verify with
`git merge-base --is-ancestor HEAD <master|main>` — and every `refs/remotes/origin/main`
probe in this skill is moot. Downstream, degrade as molt/yawn do: a
missing prerequisite yields an explicit skip with a one-line reason, never a
fail. Concretely: step 9's ancestry checks compare against the local default
branch; step 10 checks only explicitly supplied local cleanup targets against the
default branch — there are no remote branches nor merge requests to inspect.

## Reflect and update

1. **Reflect**: what worked, what didn't, what was surprising.
   **Temporary-candidate report:** before disposing this
   session, run the report-only host scan for the current runtime and session.
   Resolve the repo root as above; supply the exact runtime and session id from
   the live session metadata (do not infer an id from a path):
   ```bash
   RUNTIME=codex       # set to the exact runtime: claude, codex or pi
   SESSION_ID='id-from-live-session-metadata'
   python3 "$IDH_ROOT/scripts/tmp_report.py" --runtime "$RUNTIME" \
     --scope roar --repo "$PROJECT_REPO" --session-id "$SESSION_ID" \
     --exclude-session-id "$SESSION_ID"
   ```
   Reading the report: `runbooks/tmp-report.md`.
2-3. **Review completed merges and capture**: follow `runbooks/capture.md` in the
   wrap-up worktree; a refused or pending capture is reported in step 11.
4-5. **Sweep and report findings**: follow `runbooks/sweep.md`; follow-up tickets go
   in the single wrap-up bundle.
6. **Update project docs** if pipeline, data contract, or methodology changed.

## Bundle and fast track

Roar creates **at most one project branch/worktree** for all wrap-up changes:
follow-up tickets, project documentation and factual journal capture. Reuse a
suitable existing unmerged branch when available. Otherwise create one wrap-up
branch after the task merge. Do not create separate ticket, docs or memory PRs.
Start this branch before the first write; all writes stay inside the project.

After completing the ticket checks in steps 7–8, commit the complete bundle,
push it and open **one PR**. Fast-track it: on a gated base
(`skills/merge/SKILL.md` § Gated base) write its gate record and
merge per `skills/merge/SKILL.md` § Gated base, both as one background command (exit 2: record again
on the new head); elsewhere pass the project's required checks and enable auto-merge
using its supported merge method. This is standing authorization for roar's bounded wrap-up bundle;
no further confirmation is needed. Do not bypass failing checks or protected
branch requirements. Hoard, suggested in lair’s conclusion, remains a separately
invoked and reviewed workflow, launched in a new `/clear` session.
A failed check or submission leaves the one branch preserved and reported.
Do not wait for the bundle's checks: step 9's exit check lets the
worktree go once the branch is pushed and auto-merge is armed, or, on a gated
base, once a passing gate record covers the bundle's candidate.

## Close and clean up

7. **Close** the ticket if still open, then **check that the close claims of
   every recently merged PR actually ran** — not only this session's. One
   script runs steps 7-10's mechanical parts (close, close claims, tracker
   detection, preflight, worktree exit check and removal, explicit branch cleanup) and ends with a one-screen report; the
   judgment around it stays here. Run the first half now:

   ```bash
   ROAR_SKILL_MD="<loaded-roar-SKILL.md>"
   ROAR_DIR="$(cd -P "$(dirname "$ROAR_SKILL_MD")" && pwd -P)"
   "$ROAR_DIR/close-and-clean.sh" --phase before-exit --ticket NNNN --days 7
   ```

   In every phase here and in steps 9-10, the script's exit code and report
   are the verdict for what the script checks: do not repeat its fetches,
   ancestry or OID checks, or re-run a phase that exited 0, to confirm it. A
   phase this skill tells you to run later (step 9's exit check, with its
   fresh preflight) is a new run, not a confirmation. Ownership of the tree
   and branches you name stays your judgment.

   Exit codes, `CLOSE`/`CLAIMS` lines, `DROPPED` repair: `references/close-and-clean.md` (step 7). Omit `--ticket` when there is
   none. Not in a worktree: use `--phase all` with step 10's explicit cleanup
   targets and skip step 9; with no targets, cleanup deletes no branches.
8. **Check for tracking ticket**: if the closed ticket has a parent, check whether all sibling sub-tickets are now closed.
    - All closed → integration review: re-read all child diffs, run full test suite, verify exit criteria, and run a **repo-wide union sweep for the change class** (stale refs, moved/renamed paths) — a green suite does not exercise the build graph, so a dangling build reference survives every per-PR check. It is caught only by grepping the whole tree for the class of change at integration, not per-PR.
    - Any open → do nothing, tracker stays open.

    The script's `TRACKER: INTEGRATION-REVIEW-DUE <parent>` line is this
    check; on that hit, perform the integration review above — the script
    detects, it does not review.
9. **Exit worktree** (if in one):
    Remove only a worktree owned by this session for the completed ticket/PR,
    or explicitly handed over for that task with proven ownership. Ancestry,
    branch-name similarity and a merged PR alone do not establish ownership.
    If ownership is uncertain, keep it and name it in step 11. A tree another
    session or agent holds stays; it is left to `/molt` or `worktree-gc`.

    a. From inside the worktree, after the last wrap-up commit, run the exit
       check. Pass `--bundle-branch` only for the `roar-*`
       wrap-up branch this run created after the task merge, never the task
       branch or a reused branch:

       ```bash
       ROAR_SKILL_MD="<loaded-roar-SKILL.md>"
       ROAR_DIR="$(cd -P "$(dirname "$ROAR_SKILL_MD")" && pwd -P)"
       "$ROAR_DIR/close-and-clean.sh" --phase exit-check [--bundle-branch roar-…]
       ```

       What the exit check does and how to clear `PREFLIGHT: DIRTY`:
       `references/close-and-clean.md` (step 9a).

    b. `EXIT: READY` → `cd` to the main checkout, then run the `after-exit`
       command the report prints (run as `"$ROAR_DIR/close-and-clean.sh" …`;
       the READY line prints it bare), adding step 10's remote target.
       `after-exit --remove-worktree` runs the removal-mode `.tmp/` gate before
       unlocking the tree (hunt locks it) and running `git worktree remove`.
       The removal gate's rules (step 9b): `references/close-and-clean.md`. Never `--force`.
       An auto-merge-armed bundle is named in step 11 as pending forge
       integration and does not block the `/clear` verdict; nothing re-checks
       it later, so a check that fails afterwards shows only on its merge
       request. On a gated base the exit check needs the merge request OPEN
       with a passing gate record (or MERGED), and the bundle stays a pending
       item in step 11 until it reads MERGED: if the background merge stops
       (a moved base), nothing else lands it.

    c. `EXIT: KEEP-PENDING` or exit 2 → `cd` to the main checkout, no
       removal, and report the kept tree and the pending integration in
       step 11.

    No-forge repo: the exit check compares against the local default branch.
    Skip this step if not in a worktree. A worktree a subagent created and
    locked itself is left to `worktree-gc` once its branch is merged.
10. **Clean only the completed task** — roar cleans only the completed task's
    explicitly identified closed-ticket/merged-PR branches and owned worktrees.
    Other branches and worktrees remain, even when merged. Repository-wide
    housekeeping belongs to lair/molt.

    The `after-exit` command step 9's exit check prints already names the
    worktree and its local branch. Add each actual merged PR's source branch and full head
    OID from its durable merge/review evidence. Record these coordinates before
    worktree exit. For a task with multiple completed PRs, repeat the options;
    do not discover candidates by enumerating refs, matching ticket prefixes,
    or adopting a freshly reread mutable branch tip as approval.

    ```bash
    ROAR_SKILL_MD="<loaded-roar-SKILL.md>"
    ROAR_DIR="$(cd -P "$(dirname "$ROAR_SKILL_MD")" && pwd -P)"
    "$ROAR_DIR/close-and-clean.sh" --phase after-exit \
      --remove-worktree "$WORKTREE_PATH" \
      --local-branch "$COMPLETED_PR_BRANCH=$COMPLETED_PR_HEAD_OID" \
      --remote-branch "$COMPLETED_PR_BRANCH=$COMPLETED_PR_HEAD_OID"
    ```

    Target options, fetch and refusal mechanics (step 10):
    `references/close-and-clean.md`. Retained targets are reported for later
    handling; do not broaden the cleanup scope.

11. **Report** the completed work and any pending factual capture. Do not offer
    rule changes or interpreted memories. End with a context verdict.
    Pending means anything this step reports as pending: an unmerged PR,
    running CI, an agent still running, a visible pending capture or
    unintegrated capture branch (step 3), a kept worktree or unpushed or
    failed bundle (step 9), or an unresolved close claim (step 7). An
    auto-merge-armed wrap-up bundle that passed step 9's exit check does not
    block the verdict: its content is pushed and the forge will merge it, so
    the verdict line names its merge request. On a gated base a bundle not
    yet MERGED is pending: name it, and do not say "safe to `/clear`". When nothing is pending, say
    "State saved — safe to `/clear`"; otherwise name each pending item, since
    only then has roar written everything durable. Advise `/clear`, never
    `/compact`.

Note: STATE.md is updated on main during `/lair`, not here. Worktree GC
belongs to housekeeping (`/molt`), not here: roar exits and disposes of its
OWN merged worktree (step 9) and touches nothing outside it. A repo-wide GC
from roar would remove worktrees that are live session base cwds (a
merged-and-pruned branch reads `[gone]` even while sessions still sit in the
tree), stranding those sessions in unregistered husk dirs.
