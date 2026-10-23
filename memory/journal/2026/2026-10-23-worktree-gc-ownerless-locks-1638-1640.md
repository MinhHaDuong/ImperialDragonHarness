# Worktree GC: owner-less locks (PRs 1638 and 1640)

Date: 2026-10-23
Project: ImperialDragonHarness

## Context

A climate-finance-het /molt found four worktrees locked with `(pid 1 …)`
by a Codex /hunt: inside its pid namespace `$PPID` reads 1. On the host
pid 1 is init, always alive, so `worktree-gc.sh` skipped those trees and
molt step 0 aborted every sweep. That session opened PR 1638, then
handed review, merge and roar to session .agents on doudou and stood
down. PR 1640 followed at the author's request.

## Events

- PR 1638 round 1 reclaimed pid-1 locks as stale. The red-team seat
  (openai/gpt-6.1-sol) blocked it: a live sandboxed session can be
  invisible to the live-cwd rail. The author chose to keep pid-1 locks
  as in use.
- PR 1638 rounds 2-4: the red team found three successive holes in the
  lock-reason parser (two `(pid` groups, a pid past pid_max, a second
  `(pid` without a trailing space). None is produced by any writer.
  Round 5 REVIEWED; /verify-gate APPROVED fa5fc829 in round 1; merged as
  4eadcd38.
- The same PR fixed a separate defect: uutils `readlink` 0.10.0 (doudou)
  stops at the first unreadable link, `/proc/1/cwd` sorts first, so the
  batch read of live cwds returned nothing.
- PR 1640 reclaims the two harness owner-less shapes after 72 h of git
  inactivity on a tree with no work. Round 2 found real data loss: this
  repo's `.gitignore` is `*`, `git status` omits ignored files, and
  `git worktree remove` deletes them. The clean check now lists ignored
  files and tolerates only regenerable caches and `.tmp/`.
- PR 1640 rounds 3-4 hardened the unlock against concurrent re-locking
  (atomic claim, restore, orphan recovery, ~55 script lines). The author
  judged those scenarios theoretical, and the machinery was removed in
  97b4508d.
- PR 1640 round 5: the remaining blocker was the stated residual (a live
  sandboxed session idle 72 h after merge, before /roar, loses its
  tree), accepted as dissent. /verify-gate refused because a docs-only
  commit (0c07558a) came after the review. Merged on author authority as
  e5ca1f77, after a passing gate record on padme.
- During the merge-body edit of 1638, `gh pr edit --body-file` replaced
  the gaze attribution block; it was restored from the PR edit history.

## Outcome

- Locks with no checkable pid are kept, except the two harness shapes
  reclaimed after 72 h idle (`WORKTREE_GC_OWNERLESS_IDLE_HOURS`).
- `worktree-gc.sh`: 315 lines after 1638, 404 after 1640.
- Review cost: five gaze rounds on each PR.

## References

PRs 1638 and 1640; author decision comment issuecomment-6371861949;
journal entries 2026-10-23-review-attribution-pr1638 and -pr1640.
Not ticketed: `worktree-tmp-guard.py` treats any `.tmp/` string in a
branch's commit messages as a citation and retains the tree.
