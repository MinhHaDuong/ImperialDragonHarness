# Sweep runbook

When roar runs this: roar steps 4-5, after capture, on the ref and not the working tree.

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
   Resolve the loaded helper root in the same invocation: `<loaded-SKILL.md>` is roar's own SKILL.md, the file that points here (absolute path supplied when loading it); the `dirname/../..` expression resolves from `skills/roar/` to the harness root, so never substitute this runbook's path.

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
   on files main no longer has. Enumerate with
   `git ls-tree -r --name-only refs/remotes/origin/main -- <dir>` and read with
   `git show refs/remotes/origin/main:<path>` — never `git checkout <ref> -- <path>`, which
   writes the index.
 Record qualifying follow-up tickets in the single wrap-up branch: `tickets/erg new "<title>"`, fill the body, `erg validate` it, then include it in the wrap-up commit — don't skip the commit; an uncommitted draft is destroyed by step 9's worktree exit. Apply the severity floor (`rules/workflow.md` § Autonomous action), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.
5. **Report related findings** from the sweep. Do not turn experiences into
   unsolicited standing tests, rule proposals or crystallisation tickets.
