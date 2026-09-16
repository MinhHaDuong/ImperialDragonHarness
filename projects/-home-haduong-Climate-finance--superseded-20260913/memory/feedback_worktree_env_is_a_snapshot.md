---
name: feedback_worktree_env_is_a_snapshot
description: "A worktree's .env is a point-in-time copy; when main changes credential selection, long-lived worktrees fail credential tests for a reason that is not in the diff"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-27T19:15:37.877Z
---

`.worktreeinclude` copies `.env` into a worktree **at creation time**. It is a
snapshot, not a link. A long-lived worktree therefore drifts from the primary
checkout's `.env` — and the drift surfaces as a test failure that looks like
someone else's code defect.

Seen 2026-07-27 (ticket 0354): after merging main,
`test_keys_line_selects_every_consumed_credential` failed. The test had just been
rewritten by main's ticket-0364 commits (HAL credential selection), so the
obvious reading was "main is red, file a ticket per the no-CI rule". Wrong: the
worktree's `KEYS=` line predated 0364, and the primary checkout's was already
correct. Refreshing that one line from the primary `.env` turned it green. `.env`
is git-ignored, so nothing about the PR was ever affected.

**How to apply:** when a credential/env test fails in a worktree after merging
main, compare the worktree's `.env` against the primary checkout's *before*
attributing the failure to main. A probe worktree created with a bare
`git worktree add` has no `.env` at all, so the test **skips** there — an
inconclusive result that is easy to misread as a pass. Diff the relevant line
directly instead, and never echo the values.

**Why:** the no-CI rule ("failures your branch did not cause belong to main and
get their own ticket") is right, but it presumes the failure is in the tree.
Machine-local config drift is a third category, and it produces a false ticket
if not ruled out first (→ [[feedback_no_ci_local_merge_gate]],
[[feedback_env_file_no_override]]).
