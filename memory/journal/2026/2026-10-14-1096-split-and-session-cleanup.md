# 1096 split after its design session ended early; worktree and branch census — 2026-10-14

Project: ImperialDragonHarness. Session: interactive, Claude Code, padme.

## Context

The author's 1096 design-discussion session (tmux `d1096`, launched
18:05 local) delivered PR #1400 (design document, three panel rounds,
author answers). The author had then asked it to turn 1096 into a design
ticket, close it, and open a separate implementation ticket. That did not
happen: local branch `t1096-design-close` existed with no commits beyond
`origin/main`, and 1096 stayed open with label `deferred`.

## Observations

- `d1096` was still running at ~22:15 local, its conversation moved to a
  background session (`b718c074`). Both processes had as cwd
  `.claude/worktrees/t1096-3763862`, which no longer existed on disk
  (`/proc/<pid>/cwd` read `(deleted)`). Its branches were all ancestors of
  `origin/main`.
- Two 1097 worktrees (`roar-1097-3830949`, `t1097-3833540`) were still
  locked, with lock reasons naming pid 3830949, which no longer existed. Both
  were clean and merged (#1398, #1401). These coincide with the
  ExitWorktree refusal recorded when 1097 was reopened (#1405), later
  addressed by #1407 (1077) and #1409 (1098).
- `explore-readback-same-call` (`roar-1403-1404-1408`) was unlocked, clean,
  merged (#1410), with no process using it.
- The `{pid}` worktree discriminator is the pid of a transient `bash -c`, so
  it does not identify a live session; liveness was read from process cwds.
- PR #1414 had all ten checks green, `mergeStateStatus: CLEAN` and
  auto-merge armed, yet stayed OPEN across several reads over some minutes;
  a direct `gh pr merge --merge` landed it (5d107443). Cause not established.
- The first PR body draft used "closes #1096"; on GitHub #1096 is an
  unrelated pull request number. Reworded to `**Ticket:** 1096` before merge,
  which `erg-pr-merge` normalized.

## Outcome

- PR #1414 merged: 1096 retitled as the design ticket, `deferred` removed,
  design exit criteria ticked, closed and archived; new ticket 1100 carries
  the implementation (round-3 plan of record, children 0-4 listed, not yet
  filed); 1099 re-pointed to `Blocked-by: 1100`.
- With the author's approval: the three stale worktrees removed (two
  unlocked first), seven merged local branches deleted with `-d` after
  ancestry checks, tmux `d1096` and its background session stopped.
- With the author's approval: remote branches `raid-1080-prep`,
  `raid-1089-prep`, `t1084-roar-close-and-clean` (all commits
  patch-equivalent on main per `git cherry`) and `dream/2026-10-07`
  (pre-rewrite head of merged #1250; all its files present on main) deleted.
  `archive/review-1319-20261013` kept. STATE.md's "historical rewritten
  branches are preserved" no longer describes those four.
- Remaining remote branches: `main`, `archive/review-1319-20261013`,
  `ci-pytest-guard-speed` (open PR #1415, another session).
