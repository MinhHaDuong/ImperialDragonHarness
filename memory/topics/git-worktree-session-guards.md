# Site practice: git, worktrees and parallel sessions

Scope: git in worktrees, cleanup, sessions sharing a checkout or refs, and the
primary checkout as the author's workspace. Authority: `rules/git.md`,
`rules/claude-code.md`, `rules/prose/workpackages.md`.

## Current guidance
- **The primary checkout is the author's workspace** (author, 2026-11-01, ticket 1372; now `rules/git.md` § Branch and commit): agents work on branches and never commit there. The author's direct-to-main backdoor is per-command, `ALLOW_MAIN_COMMIT=1 git -c idh.mainGuard=warn commit` — `hooks/pre-commit` also refuses main commits in the primary (PRs 2129, 2131) ([1372](../journal/2026/2026-11-01-author-workspace-rule-1372.md)).
- When VS Code `files.autoSave` is off, `on-start-context.sh` prints one declarative line and writes the setting only on a yes (padme: `afterDelay`, PR 2130). Edit the author's open files only in an author-started turn, after saying you take the pen (workpackages.md).
- Isolation is plain worktrees (add, lock, `cd`); `EnterWorktree` is retired (author, [1077](../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md)); hunt chains add && lock with a `$PPID-$RANDOM` suffix (an unchained failed add locked the spawner's tree, [b6aabf](../journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md)).
- rtk excludes `^git` on padme and doudou since 2026-10-09 (`rtk hook check`; `rules/git.md` still governs SHA reads) ([1078](../journal/2026/2026-10-09-rtk-git-exclusion.md)). Settled by the author 2026-11-01 (ticket 1373): the 1366 exception lives here, not in `rules/git.md` — a push by commit id (`<oid>:<ref>`) lands or is refused, so its exit code answers; a push by ref name can exit 0 sending nothing after a rewound ref ([1366](../journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md), [2035](../journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md)).
- Sync local main after each merge: `$IDH_ROOT` helpers run from the primary checkout, a stale one re-ran fixed bugs (PR 1568, raids page).
- `branch -d` refuses patch-equivalent merged branches; `-D` ran on author authorization ([1644](../journal/2026/2026-10-23-branch-sweep-1644.md)); `update-ref -d` deletes a branch another worktree holds, where `branch -D` refuses ([1374](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md)). The classifier refuses force-with-lease, `branch -D`, `push --delete` despite the Bash allow (narrow allow rules fixed them 2026-10-29); never retry, hand the author a `!` command (native).
- `worktree-gc.sh` reads live cwds lazily (353 s → 76 s, [1583](../journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md)); owner-less lock shapes go after 72 h idle with ignored files checked (dissent: a live sandboxed session idle 72 h loses its tree, [1638/1640](../journal/2026/2026-10-23-worktree-gc-ownerless-locks-1638-1640.md)); a `{pid}` in a name proves no liveness (1096).
## Hazards
- `git worktree remove` deletes ignored files; `.gitignore` is `*`, so porcelain status misses them (1095, 1640).
- Shared checkout: local main carried commits into a peer's PR (#1145); `git add tickets/` swept a peer's file; a read-only reviewer switched the primary's branch (#1183); one VS Code window's sessions share a worktree (native). Untracked private skill links change the primary's test results (1091); an uncommitted edit in the installed-harness primary reaches live sessions (0887); a restart resets cwd to the primary (1077). Residual (1077): restore/checkout aimed at another tree has no guard.
- A forced notes fetch by a process sharing refs rewinds a local append. `idh.mainGuard` enforces on padme/doudou since 2026-10-27; until 2026-11-03 check `<git-common-dir>/idh/main-journal.jsonl`. A forked `/gaze` resolves PRs in the session's base repo.
## Open questions
- Does the `rules/git.md` stash ban ("in a shared checkout", stack repo-global) cover a session's own worktree? Ticket 1437. (hypothesis: shared primary as common cause) (`worktree-tmp-guard.py` keeps trees whose commits cite `.tmp/`.)
## Fallback
## Retired

- rtk-rewrite refusal catalogue and remedies, 2026-10-09 census counts: retired by the rtk exclusion (1078) and EnterWorktree's retirement (1077, PR #1407).
- Loop-era cleanup recipes: retired by `rules/git.md` § Branch cleanup (PR #1374).
- Roar's delete-then-restore compensation and parser defects: removed by the PR #1374 scope revision.
- PR #1374 merge-on-code-review and the 1090/1098 roar turn measurements: moved to the raid and merge department.
- Shared annotation base (1016, WAVE_BASE) and parallel-ref annotation collisions: superseded by WAVE_BASE practice, raid department.
- Held cross-session messages and `crossSessionInbound`: settled 2026-10-12.
- PR #1300 branch held by a stale agent worktree: one-off, superseded by GC and roar task scope.
- `~/.claude/CLAUDE.md` as a link to `AGENTS.md`: removed by PR 1462 ([docs refresh](../journal/2026/2026-10-19-docs-refresh-and-global-claude-retirement.md)); absent on padme 2026-10-30.
- "Main is read-only, sole exception manuscript prose" as the whole workspace rule: retired by the 2026-11-01 author-workspace ruling (rules/git.md, ticket 1372).

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [1077](../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md), [rtk exclusion](../journal/2026/2026-10-09-rtk-git-exclusion.md), [census](../journal/2026/2026-10-09-worktree-isolation-census.md), [1074](../journal/2026/2026-10-09-close-1074-guard-refusals.md), [raid 1072](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md), [PR 1253](../journal/2026/2026-10-08-haiku-review-delay.md)
- [raid 1084-1086](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md), [PR 1374 revision](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md), [PR 1374 evidence](../journal/2026/2026-10-13-pr1374-review-evidence/gate-and-author-comments.md), [1090 remeasure](../journal/2026/2026-10-14-roar-remeasure-1090.md), [1098](../journal/2026/2026-10-14-roar-exit-check-1098.md), [1095](../journal/2026/2026-10-14-1095-design-panel-pr1399.md), [1096](../journal/2026/2026-10-14-1096-split-and-session-cleanup.md)
- [#1145](../journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md), [1015](../journal/2026/2026-10-02-raid-1015-annotation-collision.md), [0853 raid](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [1008](../journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md), [WAVE_BASE](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md), [0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md), [#1183](../journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md), [0887](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md), [2026-10-06](../journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md), [PR 1300](../journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md), [arena 1053](../journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md), [cross-repo](../journal/2026/2026-10-12-cross-repo-session-gaze-forks.md), [1091/1092](../journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md), [relocation](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- New: [1644](../journal/2026/2026-10-23-branch-sweep-1644.md), [1638/1640](../journal/2026/2026-10-23-worktree-gc-ownerless-locks-1638-1640.md), [PR 1583](../journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md), [b6aabf](../journal/2026/2026-10-28-raid-b6aabf-worktree-adoption.md), [1366](../journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md), [PR 2035](../journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md), [author workspace 1372](../journal/2026/2026-11-01-author-workspace-rule-1372.md)
- Legacy notes: [git in a worktree session](../reference_git_in_a_worktree_session.md), [branch-cleanup incidents](../reference_branch_cleanup_incidents.md); native notes quoted in the smelt annex.
