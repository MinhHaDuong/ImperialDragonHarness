# Site practice: git, worktrees and parallel sessions

Scope: checkouts, cleanup and shared refs. Authority: `rules/git.md`,
`rules/claude-code.md`, `rules/prose/workpackages.md`.

## Current guidance

- The primary is the author's workspace; agents commit on branches. The per-command backdoor is `ALLOW_MAIN_COMMIT=1 git -c idh.mainGuard=warn commit`; pre-commit also refuses main in the primary (1372, PRs 2129/2131) [workspace]. Author-open files: only in an author-started turn, after taking the pen. Autosave off prompts once; the setting changes only on a yes (padme `afterDelay`, PR 2130).
- Isolation uses plain worktrees: add && lock, then `cd`; `$PPID-$RANDOM` distinguishes children. An unchained failed add locked the spawner's tree [adoption]. `EnterWorktree` is retired [isolation]. A restart resets cwd to primary; another tree's restore/checkout still has no guard.
- rtk excludes git on both hosts (1078); SHA reads still follow `rules/git.md`. The 1373/1366 exception is limited to `<oid>:<ref>` pushes: their exit code answers. Ref-name pushes can send nothing after a rewind and still exit 0 [push]. Sync local main after each merge: primary helpers otherwise rerun old bugs.
- `branch -d` refuses patch-equivalent branches; `-D` needed author authority (1644). `update-ref -d` bypasses worktree occupancy where `branch -D` refuses (1374). Narrow allow rules fixed observed classifier refusals; a new denial follows `rules/claude-code.md`, never a verbatim retry.
- GC lazily reads live cwds; owner-less locks expire after 72 h idle, with ignored files checked. Dissent: a live sandboxed session idle 72 h can lose its tree; a pid in a name proves no liveness (1096, 1638/1640). `worktree-tmp-guard.py` keeps commits citing `.tmp/`.

## Hazards

- Worktree removal deletes ignored files; porcelain can miss them (1095/1640). A setup copy or link is expendable only if its primary counterpart resolves outside the candidate: direct and parent-directory links once pointed to the sole copy being removed (1406, fixed PR 2216) [copy].
- Shared checkout failures: local main carried commits into a peer PR (#1145), broad ticket adds swept a peer file, a reviewer switched primary (#1183), and one VS Code window shares its tree. Untracked private skill links alter tests (1091); installed-primary edits reach live sessions (0887).
- Shared refs: forced notes fetch rewinds local appends; forked gaze resolves PRs in its base repo. Main guard remains enforcing on both hosts; its dated watch ended [pins].
- Idle branch names do not establish scope or redundancy. Two held unlanded filings; another sounded cross-project but held harness tickets [stranded]. A locked orphan's unpushed commit surfaced only through its ahead count [orphan]. Uncommitted split drafts blocked sync and their IDs were reused before recovery [split].

## Open questions

None exposed in this pass.

## Retired

- Classifier advice “never retry, hand the author a ! command”: superseded by the narrow-allow fix already recorded in the accepted sixth report and current `rules/claude-code.md` (literal rewrite or log/skip).
- The blanket `.gitignore` example is episode-specific; the general ignored-file deletion caveat remains.
- Main-guard watch through 2026-11-03: ended; author-reviewed Commission records its outcome (1452), not a continuing watch.
- GC's 353 s → 76 s measurement: dated optimization history; expiry, ignored-file and liveness caveats remain above.
- Earlier Retired entries move to history in the previous page; their original source links remain below.

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [1077](../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md), [rtk exclusion](../journal/2026/2026-10-09-rtk-git-exclusion.md), [census](../journal/2026/2026-10-09-worktree-isolation-census.md), [1074](../journal/2026/2026-10-09-close-1074-guard-refusals.md), [raid 1072](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md), [PR 1253](../journal/2026/2026-10-08-haiku-review-delay.md)
- [raid 1084-1086](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md), [PR 1374 revision](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md), [PR 1374 evidence](../journal/2026/2026-10-13-pr1374-review-evidence/gate-and-author-comments.md), [1090 remeasure](../journal/2026/2026-10-14-roar-remeasure-1090.md), [1098](../journal/2026/2026-10-14-roar-exit-check-1098.md), [1095](../journal/2026/2026-10-14-1095-design-panel-pr1399.md), [1096](../journal/2026/2026-10-14-1096-split-and-session-cleanup.md)
- [#1145](../journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md), [1015](../journal/2026/2026-10-02-raid-1015-annotation-collision.md), [0853 raid](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [1008](../journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md), [WAVE_BASE](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md), [0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md), [#1183](../journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md), [0887](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md), [2026-10-06](../journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md), [PR 1300](../journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md), [arena 1053](../journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md), [cross-repo](../journal/2026/2026-10-12-cross-repo-session-gaze-forks.md), [1091/1092](../journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md), [relocation](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- New: [1644](../journal/2026/2026-10-23-branch-sweep-1644.md), [1638/1640](../journal/2026/2026-10-23-worktree-gc-ownerless-locks-1638-1640.md), [PR 1583](../journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md), [b6aabf](../journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md), [1366](../journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md), [PR 2035](../journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md), [author workspace 1372](../journal/2026/2026-11-01-author-workspace-rule-1372.md)
- Legacy notes: [git in a worktree session](../reference_git_in_a_worktree_session.md), [branch-cleanup incidents](../reference_branch_cleanup_incidents.md); native notes quoted in the smelt annex.
[workspace]: ../journal/2026/2026-11-01-author-workspace-rule-1372.md
[adoption]: ../journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md
[isolation]: ../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md
[push]: ../journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md
[copy]: ../journal/2026/2026-11-05-t1406-worktree-copy-review.md
[pins]: ../journal/2026/2026-11-07-smelt-1451-follow-ups-1452.md
[stranded]: ../journal/2026/2026-11-07-molt-stranded-ticket-branches.md
[orphan]: ../journal/2026/2026-11-04-t1444-orphaned-worktree-rescue.md
[split]: ../journal/2026/2026-11-07-stranded-1444-split-blocked-sync.md



## Fallback
