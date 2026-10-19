---
name: roar
description: "Post-task wrap-up. Reflects on completed work, updates project state, cleans up branches."
disable-model-invocation: false
user-invocable: true
---

# Roar — post-task wrap-up

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
(Precedent: Œconomia manuscript wrap-up, 2026-07-07.)

## Pre-check

If the merge was only queued (checks were pending), ask the outcome once:

```bash
ROAR_SKILL_MD="<loaded-roar-SKILL.md>"
IDH_ROOT="$(cd -P "$(dirname "$ROAR_SKILL_MD")/../.." && pwd -P)"
"$IDH_ROOT/skills/merge/erg-pr-status" N
```

Exit 0 merged, proceed; 2 pending, stop and say the merge has not landed yet
(do not wait or loop; the user or a later step re-runs `/roar`); 1 failed,
report it. Then verify the branch has been merged before proceeding:
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
   **Temporary-candidate report (ticket 1118):** before disposing this
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
   The helper scans candidates across its configured host-wide roots. When
   session flags are supplied, history attribution is limited to this session
   and linked child sessions; candidates without a match in that scoped
   history remain visible as unattributed. The reporting session is excluded
   from citation attribution while its child graph remains available;
   candidates mentioned only by the current session remain unattributed. If
   the runtime or session id cannot be established, pass the known runtime and
   omit both session flags. It never
   deletes candidate data. A citation is not proof of creation; `created`
   appears only for a matching native Claude/Codex call and result id, explicit
   zero exit status, and one direct command targeting the exact candidate. Do
   not copy raw history commands into the wrap-up.
2. **Review completed merges**: identify each reviewed merged PR from the
   project's git history and forge, then capture its review attribution in
   step 3. Report a capture failure if the review trail lacks required facts.
3. **Capture significant project experiences**, if any, before removing the
   worktree. Write and commit an append-only entry under the project's
   `memory/journal/YYYY/YYYY-MM-DD-<slug>.md`. Record context, observable events,
   outcome and decisions already made, with references. Include positive and
   negative experiences: novelty, surprise, a consequential failure or success,
   a near miss, or a departure from an existing principle are candidate signals.
   Routine completion alone does not require an entry. Keep it factual, without
   judgment, inferred lessons, rule proposals or interpreted memories.

   Resolve the project repository first. Use the single
   wrap-up branch/worktree described below. Capture only there; never in the
   harness because the loaded skill lives there. There is no private companion
   store — the encrypted-in-repo policy (author decision 2026-10-02, PR #1112)
   supersedes it: judge the audience at capture, before the first byte is
   written, and material not cleared for the repository's public audience
   enters that same repository as age ciphertext through the project's pinned
   capture mechanism (in the harness, `$IDH_ROOT/scripts/memory-capture.sh`, which pins
   the encrypt command, the per-project key under ~/.config/keys/memory/ and
   the judgment point; plaintext never lands in the working tree). Include the
   capture in the single wrap-up bundle, preserve unrelated
   changes, and follow the project's branch/integration policy. A refused write
   or failed commit remains a visible pending capture; do not switch to the
   harness or a native memory directory. An unintegrated capture branch must be
   preserved and reported before worktree cleanup. Do not invoke memory-sweep
   to derive lessons or propose rules during roar.

   **Capture review attribution for every reviewed merged PR**, even when
   routine completion produces no significant-experience entry. Use the fixed
   lines in [the attribution contract](../../docs/2026-10-02-reviewer-attribution-design.md#4-the-attribution-record):
   first line `kind: review-attribution`, PR/date/project, writer runtime,
   verbatim provider-qualified full model id and effort, then one named
   `reviewer:` line per review attempt with `status: ran|failed|skipped`.
   Include `model-version=` whenever the provider exposes it. Record findings
   as repository-relative `path:line` with `adopted: yes|no`; identical anchors
   across reviewers are shared catches. Keep a stable name-or-role value for each actual reused reviewer context,
   including repeated rounds and regression checks; retain every raw attempt.
   Use distinct values only for genuinely separate contexts or processes. The
   exact seat/runtime/model/model-version identity unions repeated-attempt anchors;
   source revision, round and evidence references belong in opaque context.
   A failed authentication is a named failed attempt, not a clean review.
   No initial `defect-confirmed:` placeholder is written.

   Read identities, attempt outcomes and adoption decisions from the actual
   review trail (session outputs or durable PR review comments), never from
   memory or the example template. Do not reconstruct a full model id from an
   alias. When the runtime conceals the verbatim id, use the contract's explicit
   `model-state=runtime-masked · model-evidence=<repo-relative-path>:<positive-line>`
   instead of `model=` on each affected writer or reviewer; omit `model-version=`.
   Preserve durable evidence connecting that limitation to the actual attempts.
   This preserves factual capture while leaving model re-audition impossible:
   the whole PR game is excluded from model estimates and visibly counted as
   runtime-masked. Never use this state to cover unrelated missing facts.
   A reviewed PR whose record cannot name its reviewers or establish
   required facts is a **capture failure**: report the PR and missing facts in
   step 11's summary; preserve the pending capture, never silently omit it.
   Validate the complete record before writing: stream its text on stdin to
   `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)" && python3 "$IDH_ROOT/scripts/attribution_record.py" --capture "$PROJECT_REPO" --audience public`
   Replace `<loaded-SKILL.md>` with the absolute path supplied when loading
   this Roar skill; resolve the helper root in the same shell invocation.
   (use `private` for uncleared material). `PROJECT_REPO` is the resolved
   project's wrap-up worktree; the helper writes the dated
   `review-attribution-prNNNN` journal entry through `memory-capture.sh`.
   Judge the audience before constructing any file; private text stays in the
   stream, never a plaintext working-tree file. Report validation, encryption,
   overwrite or integration failures visibly. Commit successful capture in
   the same wrap-up bundle. Project installations with their own pinned capture
   mechanism must apply that mechanism with the same validated record and
   audience policy; no fallback store is authorized.
4. **Sweep for similar patterns**: review the fix just completed. Grep/audit the codebase for the same anti-pattern in other files.

   **Backfill commissioned defect fixes only.** When the completed merge has
   explicit evidence that it fixed a defect, identify its actual merged PR and
   full fix commit SHA from the project's integration history. Run the helper
   in the project's existing wrap-up worktree,
   with its full merged commit SHA and a full integration-tip SHA resolved
   from the project's `refs/remotes/origin/main`, which contains that merged fix. The
   wrap-up branch may stay below that merge; `--merged-through` proves the fix
   belongs to the actual integration history without changing its checkout.
   Supply explicit `PR=reviewed-SHA` evidence from
   the durable review trail for each past record. The evidence must establish
   the coordinates of every reviewer attempt in that record; absent or mixed
   revisions are unresolved. Never infer revisions from record context or apply
   a branch-wide SHA across attempts without supporting trail evidence.
   Resolve the loaded helper root in the same invocation:

   ```bash
   IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)" && MERGED_THROUGH="$(git -C "$PROJECT_REPO" rev-parse --verify 'refs/remotes/origin/main^{commit}')" && python3 "$IDH_ROOT/scripts/attribution_backfill.py" --project "$PROJECT_REPO" --merged-through "$MERGED_THROUGH" --defect-fix --fix-pr "$FIX_PR" --fix-commit "$FIX_SHA" --reviewed "$PAST_PR=$REVIEWED_SHA"
   ```

   Repeat `--reviewed PR=SHA` for additional supported records. This joins
   literal finding anchors to fix old-side hunks only when the reviewed file
   blob equals the first-parent fix base. Pure insertions do not cover old
   lines. Duplicate PR records, malformed/encrypted records, unknown revisions,
   drift, rename or missing files warn unresolved; never decrypt, recover
   coordinates fuzzily or write outside the project. Routine merges and merges
   without a PR identity do not commission this hook; report their visible skip.
   Keep appends in the existing single wrap-up bundle. Report the helper's
   appended/no-match/unresolved counts, including a no-covered-review no-op;
   a write error is a failure to report, never an all-clear. Backfill is factual
   and never changes original findings or adopted flags.

   **Sweep the ref, not the working tree.** The pre-check's
   `merge-base --is-ancestor HEAD refs/remotes/origin/main` exits 0 both when your branch is
   merged and when the checkout is simply *behind* main, so a green pre-check is
   no evidence the tree carries main's content — and a sweep run there reports
   on files main no longer has (2026-09-10: this step read a guard script that
   PR #869 had deleted minutes earlier, and would have returned a confident
   wrong answer had the deletion not been known). Enumerate with
   `git ls-tree -r --name-only refs/remotes/origin/main -- <dir>` and read with
   `git show refs/remotes/origin/main:<path>` — never `git checkout <ref> -- <path>`, which
   writes the index.
 Record qualifying follow-up tickets in the single wrap-up branch: `tickets/erg new "<title>"`, fill the body, `erg validate` it, then include it in the wrap-up commit — don't skip the commit; an uncommitted draft is destroyed by step 9's worktree exit (see ticket 0174). Apply the severity floor (`rules/workflow.md` § Autonomous action), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.
5. **Report related findings** from the sweep. Do not turn experiences into
   unsolicited standing tests, rule proposals or crystallisation tickets.
6. **Update project docs** if pipeline, data contract, or methodology changed.

## Bundle and fast track

Roar creates **at most one project branch/worktree** for all wrap-up changes:
follow-up tickets, project documentation and factual journal capture. Reuse a
suitable existing unmerged branch when available. Otherwise create one wrap-up
branch after the task merge. Do not create separate ticket, docs or memory PRs.
Start this branch before the first write; all writes stay inside the project.

After completing the ticket checks in steps 7–8, commit the complete bundle,
push it and open **one PR**. Fast-track it through the
project's required checks and enable auto-merge using its supported merge
method. This is standing authorization for roar's bounded wrap-up bundle;
no further confirmation is needed. Do not bypass failing checks or protected
branch requirements. Hoard, suggested in lair’s conclusion, remains a separately
invoked and reviewed workflow, launched in a new `/clear` session.
A failed check or submission leaves the one branch preserved and reported.
Do not wait for the bundle's checks: step 9's exit check lets the
worktree go once the branch is pushed and auto-merge is armed.

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

   Exit 0 clean, 1 findings, 2 could-not-look (never an all-clear: a
   `tickets/` whose `erg` does not run, an unreadable forge or a failed fetch
   all give 2; a repo with no `tickets/` directory at all gets an explicit
   `skipped` line for CLOSE and CLAIMS, per the prerequisite policy above). Omit
   `--ticket` when there is none. Not in a worktree: use `--phase all` with step 10's explicit
   cleanup targets and skip step 9. With no targets, cleanup deletes no branches. Its report lines:

   - `CLOSE: ALREADY-CLOSED` is the usual case after `/merge`;
     `CLOSED-UNCOMMITTED` means it closed and archived the ticket and you must
     commit that in the wrap-up bundle.
   - `CLAIMS`: a PR body's `**Ticket:**` line is executed by `erg-pr-merge`,
     not by the forge. Any other route — a bare forge-CLI merge, the forge's
     web UI, another machine, another session — lands the code and drops the
     claim with no output, and `erg check` passes either way (git-erg PR #334,
     2026-09-10: ticket 0276's fix sat on main while 0276 stayed open). The
     findings are `DROPPED` (ticket exists, no `Closed:` header) or
     `UNRESOLVED` (no such ticket here — renumbered, or this checkout is
     behind). The script never repairs a `DROPPED`: do it with
     `tickets/erg close <id>` plus `tickets/erg archive`, committed like any
     other change. `/yawn` step 9 does not cover this: it indexes on
     the `Closed:` header being *present*, so it is blind to a ticket that was
     never closed at all.
8. **Check for tracking ticket**: if the closed ticket has a parent, check whether all sibling sub-tickets are now closed.
    - All closed → integration review: re-read all child diffs, run full test suite, verify exit criteria, and run a **repo-wide union sweep for the change class** (stale refs, moved/renamed paths) — a green suite does not exercise the build graph, so a dangling build reference survives every per-PR check. It is caught only by grepping the whole tree for the class of change at integration, not per-PR. (2026-07-11, 0240 reorg: a merged `.mk` prerequisite kept a moved script's old flat path; per-move greps and green `make check-fast` all passed — only the integration union grep found it.)
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
       check (ticket 1098). Pass `--bundle-branch` only for the `roar-*`
       wrap-up branch this run created after the task merge, never the task
       branch or a reused branch:

       ```bash
       ROAR_SKILL_MD="<loaded-roar-SKILL.md>"
       ROAR_DIR="$(cd -P "$(dirname "$ROAR_SKILL_MD")" && pwd -P)"
       "$ROAR_DIR/close-and-clean.sh" --phase exit-check [--bundle-branch roar-…]
       ```

       It runs a fresh preflight (the step-7 result predates the wrap-up
       work), the bounded integration fetch, the ancestry check of HEAD, or
       for the bundle: its remote tip equals HEAD and its merge request is
       open with auto-merge armed. It then syncs local `main`, best effort.
       `PREFLIGHT: DIRTY` → commit (or `$IDH_ROOT/scripts/worktree-salvage.sh`)
       and re-run; the preflight removes only `.panel/` and `build/panel-head/`
       review scratch and refuses every other uncommitted file, including an
       uncommitted ticket draft (tickets 0174, 0948).

    b. `EXIT: READY` → `cd` to the main checkout, then run the `after-exit`
       command the report prints (run as `"$ROAR_DIR/close-and-clean.sh" …`;
       the READY line prints it bare), adding step 10's remote target.
       `after-exit --remove-worktree` unlocks the tree (hunt locks it) and
       runs `git worktree remove`. Git refuses a tree with modified or
       untracked files, and the branch survives removal, so no commit is
       lost; ignored files are deleted with the tree, as with any
       `git worktree remove` (scan for them: ticket 1095). Never `--force`.
       An armed bundle is named in step 11 as pending forge integration; it
       does not block the `/clear` verdict, and a later roar reports its
       merge request if a check fails.

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

    `--local-branch B=OID` and `--remote-branch B=OID` are independent,
    repeatable cleanup targets. Omit either side if there is no verified
    target there (for example, the forge already deleted the remote branch).
    With neither option, the helper deletes nothing. Repeated cleanup reports
    already absent targets; remote absence is checked at the named remote ref,
    rather than inferred from a missing tracking ref. A squash/rebase merge
    whose original head is not an ancestor is retained; patch equivalence
    may justify the wrap-up pre-check but does not authorize deletion here.

    The helper fetches only the default integration branch into its tracking ref,
    ignoring configured refspecs and opportunistic refmaps. It disables tags,
    pruning, submodule recursion and automatic maintenance, then resolves exact
    refnames, requires the supplied full OID to match, and checks ancestry
    against `refs/remotes/origin/<default>` (the local default without origin).
    `--default-branch B` overrides the default read from `origin/HEAD`, falling
    back to main. Default, current, symbolic and occupied branches remain and are reported
    as retained findings (exit 1).
    A named completed-PR branch at the integration tip is eligible; ownership
    comes from the explicit PR evidence, not its relationship to that tip.

    Immediately before local deletion it rechecks the OID and occupancy, then
    uses ordinary `git branch -d`, with its remote overridden for that command
    to `idh-roar-head-check-<approved-OID>`. Before the override it verifies that
    no configuration keys exist for that alias; a configured alias is a retained
    finding and an unreadable config is could-not-look. The nonempty unconfigured
    alias makes Git check containment in HEAD as an additional conservative guard,
    avoiding the empty-remote crash for tracked branches in Git 2.53.
    A checkout behind integration may therefore retain an otherwise eligible
    target. This retains Git's merge and worktree refusal
    without editing persistent upstream config. These prechecks are not atomic
    with deletion and do not promise safety against arbitrary concurrent ref
    writers. Remote deletion leases the supplied OID. Drift, unmerged targets
    and refused deletes are findings (exit 1); unreadable prerequisites are
    could-not-look (exit 2), never an all-clear. No delete-and-restore recovery
    or human-output parsing is used. Report retained targets for later handling;
    do not broaden the cleanup scope.

11. **Report** the completed work and any pending factual capture. Do not offer
    rule changes or interpreted memories. End with a context verdict.
    Pending means anything this step reports as pending: an unmerged PR,
    running CI, an agent still running, a visible pending capture or
    unintegrated capture branch (step 3), a kept worktree or unpushed or
    failed bundle (step 9), or an unresolved close claim (step 7). An auto-merge-armed
    wrap-up bundle that passed step 9's exit check does not block the
    verdict: its content is pushed and the forge will merge it, so the
    verdict line names its merge request. When nothing is pending, say
    "State saved — safe to `/clear`"; otherwise name each pending item, since
    only then has roar written everything durable. Advise `/clear`, never
    `/compact`.

Note: STATE.md is updated on main during `/lair`, not here. Worktree GC
belongs to housekeeping (`/molt`), not here: roar exits and disposes of its
OWN merged worktree (step 9) and touches nothing outside it. A repo-wide GC
from roar removed worktrees that were live session base cwds (2026-07-13,
ticket 0355 — a merged-and-pruned branch reads `[gone]` even while sessions
still sit in the tree), stranding those sessions in unregistered husk dirs
where git silently resolves to the primary checkout.
