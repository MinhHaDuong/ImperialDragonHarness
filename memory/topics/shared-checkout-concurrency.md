# Concurrent sessions on one checkout

Scope: episodes of 2026-10-02 to 2026-10-13 in which two or more sessions,
or a session and its subagent, acted on the same primary checkout of this
repository or on the same live user files. Each fact is dated and sourced
below; the applicable rules are `rules/git.md` (branch discipline, no stash,
anchoring git after a fork) and `rules/workflow.md` (Delegation), which this
topic does not restate or extend.

## Supported observations

Unpushable local `main` as a carrier. Direct pushes to `main` are declined by
the repository ruleset (recorded 2026-10-02 in four entries). Commits parked
on local `main` were therefore swept up by whichever session delivered next:
PR #1145 double-carried four commits SHA-identical to open PR #1143's branch,
caught only by the `cross-pr-ticket-collision` check, and was rebuilt from
`origin/main` with the session's own commits. Raid annotations parked on
local `main` landed through another session's wrap PR (#1139) under that
session's attribution; one rebase resolved PR #1138 because both copies
carried the same text. In the 0853/0937/0979/1014 raid one annotation patch
existed as three distinct commits by merge time, resolved by ordered merges,
an auto-dropping rebase and one manual three-file conflict resolution.

The shared annotation base (ticket 1016, option 1). On 2026-10-03 four
wave-1 branches forked from one annotation commit; the per-wave integration
review found zero ticket-file conflicts across all six PR pairs, against the
three divergent copies of 2026-10-02. One wave is one positive case, not a
measured rate.

Other shared-checkout events. `git add tickets/` in the shared checkout swept
a parallel session's untracked ticket into a commit, caught by
`git show --stat` and repaired before push (2026-10-03). A reviewer subagent
briefed "read-only; do not edit, commit, or push" switched branches in the
shared primary checkout and left it on `main`; the parent noticed only through
an unplanned re-read, and no damage followed (2026-10-04, PR #1183). A PR was
merged by a parallel session while its gaze round was still open; the gaze's
ESCALATE fix went through a gated follow-up PR (#1166) rather than reopening
the merged one (2026-10-03).

Live user files. A tournament session's `idh install` from a pre-merge
checkout merged harness hooks back into the live `~/.claude/settings.json`
three minutes after ticket 0887's activation removed them, a double-fire state
detected by PR #1211's review panel; during reproduction a review seat that
did not override `HOME` clobbered the same live file and restored it
sha-verified (2026-10-05). On 2026-10-06 a Vibe tournament session in the
primary checkout acted on review remarks meant for another session; because
`~/.claude/CLAUDE.md` is a symlink to `AGENTS.md`, its uncommitted `AGENTS.md`
edit reached running sessions, one of which corrected its open PR #1223
against the new text. No work was lost; the split of the two sessions' work
went to the author.

Refresh, 2026-10-08 to 2026-10-13. Parallel sessions with no shared channel
used git as the shared surface. On the tournament publication day, a Codex
session ran a late arm while a Claude session wrote the reports; the author
relayed messages and set an ownership split by file, and a fix request that
crossed the split needed separate authorisation (PR #1253). On padme, two
sessions shared the arena checkout: one created and switched to its branch,
and the other session's next commit landed on it. The commit was recovered by
cherry-pick into a separate worktree. Cross-session messages to a bypass-mode
session were held for approval, and one expired undelivered, until the author
set `crossSessionInbound: "accept"` on doudou (2026-10-12). An abandoned agent
worktree still held PR #1300's branch, so `erg-pr-merge` refused to run from
another branch and the PR went through the forge's auto-merge (2026-10-09).
The PR #1374 roar preserved a branch held in another session's locked
worktree because ownership was not established (2026-10-13).

A primary checkout that differs from a clean tree changed test results twice.
On 2026-10-12, untracked private skill symlinks in the primary checkout pushed
the skills census over budget, while the same commit passed in a worktree and
in CI (fixed by 1091, which budgets tracked cards only). On 2026-10-13 the
primary checkout was moved to a test commit and then restored, with a recorded
post-restore check. The same class appeared on 2026-09-29: hermetic tests that
faked `HOME` but ran from the checkout were red there and green elsewhere.

Cross-repo base. On 2026-10-12, a session based in another repository worked
in this harness by absolute paths after `EnterWorktree` refused the path.
Forked `/gaze` runs then resolved PR numbers against the base repository and
returned "PR not found".

## Exceptions and contrasts

The read-only reviewer episode is not a counter-example to the Delegation
rule's wording: the brief forbade edit, commit and push, and the branch switch
was none of these. Whether briefs should name branch switching is a rule
question this memory does not settle. The 1015 entry's suggestion (commit
phase annotations on a short-lived branch or in the wave's wrap PR) is the
author of that entry's proposal; ticket 1016 is the decision record.

## Hypotheses, not facts

That the shared primary checkout is the common factor in these episodes is
a connection between episodes, not an established cause: several also
involve a direct-push refusal, a symlinked instruction file, or a missing
`HOME` override.

## Refresh: cwd and stale-worktree observations (2026-10-14)

The [1077 episode](../journal/2026/2026-10-14-enterworktree-opt-in-dropped-1077.md)
retired EnterWorktree, retaining plain-git isolation. A session restart reset
cwd to primary and a relative edit reached main before being moved back to
the branch. Historical entered-session refusals above do not describe the new
un-entered path.

The [1096 cleanup census](../journal/2026/2026-10-14-1096-split-and-session-cleanup.md)
found live processes whose cwd was a deleted worktree, plus locks naming dead
PIDs. The `{pid}` discriminator came from a transient shell, so it did not
establish session liveness; the census used process cwds. Author-approved
cleanup removed the specifically identified stale trees and merged branches,
while retaining another session's open #1415 tree and the archived review
branch. This was an authorized census, not task-local roar scope expanding.

## Sources

- [Local main double-carried PR #1143's commits](../journal/2026/2026-10-02-local-main-double-carried-open-pr-commits.md)
- [Raid 1015 annotation collision](../journal/2026/2026-10-02-raid-1015-annotation-collision.md)
- [Raid 0853/0937/0979/1014 under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md)
- [Raid 1008, direct push declined](../journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md)
- [WAVE_BASE first live run](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md)
- [0938 raid, swept untracked ticket](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Reviewer switched the primary checkout's branch](../journal/2026/2026-10-04-review-subagent-switched-primary-checkout-branch.md)
- [0887 live reinstall regression](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md)
- [Two sessions, one set of routing remarks](../journal/2026/2026-10-06-two-sessions-one-set-of-routing-remarks.md)
- [Tournament publication day](../journal/2026/2026-10-08-tournament-publication-wrapup.md) and [PR 1253 review delay](../journal/2026/2026-10-08-haiku-review-delay.md)
- [PR 1300 branch held by another worktree](../journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md)
- [Arena 1053 shared checkout](../journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md) and [first half](../journal/2026/2026-10-12-t1053-arena-git-and-scoped-vram-wait.md)
- [Cross-repo session gaze forks](../journal/2026/2026-10-12-cross-repo-session-gaze-forks.md)
- [Raid 1084/1085/1086, overlay census](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md)
- [Raid 1091/1092](../journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md)
- [PR 1374 merge and roar](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md)
- [2026-09-29 relocation lessons import](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
