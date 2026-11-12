# Site practice: git, worktrees and parallel sessions

Scope: checkouts, cleanup and shared refs. Authority: `rules/git.md`,
`rules/claude-code.md`, `rules/prose/workpackages.md`.

## Current guidance

- The primary is the author's workspace; agents commit on branches. The per-command backdoor is `ALLOW_MAIN_COMMIT=1 git -c idh.mainGuard=warn commit`; pre-commit also refuses main in the primary (1372, PRs 2129/2131) [workspace]. Author-open files: only in an author-started turn, after taking the pen. Autosave off prompts once; the setting changes only on a yes (padme `afterDelay`, PR 2130).
- Isolation uses plain worktrees: add && lock, then `cd`; `$PPID-$RANDOM` distinguishes children. An unchained failed add locked the spawner's tree [adoption]. `EnterWorktree` is retired [isolation]. A restart resets cwd to primary; a subagent's `cd` may not persist between calls, so a bare `git push … HEAD` once ran from the primary and pushed nothing [f7aa]. Use `git -C` or a `(cd … && …)` subshell.
- rtk excludes git on both hosts (1078); SHA reads still follow `rules/git.md`. The 1373/1366 exception is limited to `<oid>:<ref>` pushes; a ref-name push can send nothing after a rewind and still exit 0 [push]. Sync local main after each merge: primary helpers otherwise rerun old code.
- Cleanup follows git's contract since 1500 (PR 2394): the ignored-residue rule and the `.tmp` citation gate are retired, so ignored files and `.tmp/` go with the tree (porcelain can miss them, 1095/1640); a tree holding a nested registered worktree is kept, by the preflight, roar's after-exit and `raid_land.py --cleanup` (1512, PR 2428) [1500][ce1c]. Author, 2026-11-10: prose incites cleaning up after oneself, never recycling a tree [1500]. A dead-pid tree, clean and at its upstream, is reclaimed with its branch kept (1495). GC lazily reads live cwds; owner-less locks expire after 72 h idle. Dissent: a live sandboxed session idle 72 h can lose its tree; a pid in a name proves no liveness (1096, 1638/1640).
- Classifier: compound force-push calls (with `;`, `&&`, `-q`, a redirect or `cd`) were refused; `git push --force-with-lease origin <branch>` alone in its call passed. Merging main into the branch plus a plain push keeps the reviewed head an ancestor and needs no force [ce1c][2358]. `update-ref -d` and `branch -d` after merge replace `-D`, which needed author authority (1644). A new denial follows `rules/claude-code.md`, never a verbatim retry.

## Hazards

- `worktree-exit-preflight.sh --removal` removes: it purged `.panel/` on 2026-11-08 and mid-gaze on 2026-11-09; the guard script alone deletes nothing. PR 2275 moved the purge after the residue check [tmpg][632b]. Read a script before running a "read-only" reproduction from another session.
- Outer `git worktree remove` deleted an inner registered tree's uncommitted file when `.claude/worktrees/` was ignored [1500]. A setup link is expendable only if its primary counterpart resolves outside the candidate (1406) [copy].
- Shared checkout: untracked ticket files written in the primary blocked the local main sync [4afd]; local main carried commits into a peer PR (#1145); broad ticket adds swept a peer file; a reviewer switched primary (#1183); one VS Code window shares its tree. Untracked private skill links alter tests (1091); installed-primary edits reach live sessions (0887). In JETP-observer and climate-finance-het, `core.hooksPath` points into the primary's tracked `.githooks`, so `install --hooks` from a worktree rewrites the primary's file [1478].
- Shared refs: a forced notes fetch rewinds local appends; forked gaze resolves PRs in its base repo. Main guard remains enforcing on both hosts [pins].
- Idle branch names do not establish scope or redundancy: two held unlanded filings, another held harness tickets [stranded]. A locked orphan's unpushed commit surfaced only through its ahead count [orphan]. Uncommitted split drafts blocked sync and their IDs were reused [split].

## Open questions

None exposed in this pass.

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../design/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../design/memory-v8/source-revisions.tsv).
- [1077](../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md), [rtk exclusion](../journal/2026/2026-10-09-rtk-git-exclusion.md), [census](../journal/2026/2026-10-09-worktree-isolation-census.md), [1074](../journal/2026/2026-10-09-close-1074-guard-refusals.md), [raid 1072](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md), [PR 1253](../journal/2026/2026-10-08-haiku-review-delay.md)
- [raid 1084-1086](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md), [PR 1374 revision](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md), [PR 1374 evidence](../journal/2026/2026-10-13-pr1374-review-evidence/gate-and-author-comments.md), [1090 remeasure](../journal/2026/2026-10-14-roar-remeasure-1090.md), [1098](../journal/2026/2026-10-14-roar-exit-check-1098.md), [1095](../journal/2026/2026-10-14-1095-design-panel-pr1399.md), [1096](../journal/2026/2026-10-14-1096-split-and-session-cleanup.md)
- [#1145](../journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md), [1015](../journal/2026/2026-10-02-raid-1015-annotation-collision.md), [0853 raid](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [1008](../journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md), [WAVE_BASE](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md), [0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md), [#1183](../journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md), [0887](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md), [2026-10-06](../journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md), [PR 1300](../journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md), [arena 1053](../journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md), [cross-repo](../journal/2026/2026-10-12-cross-repo-session-gaze-forks.md), [1091/1092](../journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md), [relocation](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- [1644](../journal/2026/2026-10-23-branch-sweep-1644.md), [1638/1640](../journal/2026/2026-10-23-worktree-gc-ownerless-locks-1638-1640.md), [PR 1583](../journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md), [1366](../journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md), [1495](../journal/2026/2026-11-09-roar-1495-gc-reclaim-third-round.md)
[split]: ../journal/2026/2026-11-07-stranded-1444-split-blocked-sync.md
[pins]: ../journal/2026/2026-11-07-smelt-1451-follow-ups-1452.md
- Legacy notes: [git in a worktree session](../reference_git_in_a_worktree_session.md), [branch-cleanup incidents](../reference_branch_cleanup_incidents.md); native notes quoted in the smelt annex.
[workspace]: ../journal/2026/2026-11-01-author-workspace-rule-1372.md
[adoption]: ../journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md
[isolation]: ../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md
[push]: ../journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md
[copy]: ../journal/2026/2026-11-05-t1406-worktree-copy-review.md
[stranded]: ../journal/2026/2026-11-07-molt-stranded-ticket-branches.md
[orphan]: ../journal/2026/2026-11-04-t1444-orphaned-worktree-rescue.md
[f7aa]: ../journal/2026/2026-11-10-raid-f7aac3-staging-recognition-and-receipts.md
[1500]: ../journal/2026/2026-11-10-raid-91a35c.md
[ce1c]: ../journal/2026/2026-11-10-roar-raid-ce1c5a-raid-land-nested-worktree.md
[2358]: ../journal/2026/2026-11-09-roar-pr2358-interface-context-ceiling.md
[tmpg]: ../journal/2026/2026-11-08-tmp-guard-arena-misfires-and-panel-purge.md
[632b]: ../journal/2026/2026-11-09-raid-632b19-wave2-projects-untrack.md
[4afd]: ../journal/2026/2026-11-09-raid-4afdb3-post-skill-gaze-close.md
[1478]: ../journal/2026/2026-11-09-1478-fanout-claims-rollout.md

## Fallback
