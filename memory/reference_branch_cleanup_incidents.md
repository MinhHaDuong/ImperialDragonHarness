---
name: reference_branch_cleanup_incidents
description: "Why each guard in the branch-cleanup loops exists: the deleted local main, the bare origin symref that aborted a sweep under set -e, and why -D is safer than -d after an ancestry probe"
metadata:
  node_type: memory
  type: reference
  modified: 2026-09-09T18:00:00Z
---

Evidence behind the two loops in `rules/git.md` § Branch cleanup (ticket 0242,
ratcheted by `tests/test_branch_cleanup_recipes.py`). Each guard cost a branch.

- **`main` and current-branch guards.** Local `main` is always an ancestor of
  `origin/main`, and so is the branch you are standing on right after a merge.
  With the primary checkout detached, `git branch -d main` succeeds: an
  unguarded loop deleted local main during a `/roar` hygiene pass (2026-06-10),
  recovered with `git branch --track main origin/main`.
- **The `case` guard on the remote sweep.** `for-each-ref refs/remotes/origin/`
  also yields the bare `origin` symref, whose `${ref#origin/}` strips nothing,
  so the unguarded loop runs `git push origin --delete origin`. That fails, and
  under `set -e` it aborts the sweep on its first iteration — leaving every
  stale branch in place while the run looks like it did something. Bit the loop
  on first use (2026-08-14, polycentric_activity, ten stale remote branches with
  zero open merge requests).
- **`-D`, not `-d`.** `-d` checks merged-into-HEAD, not merged-into-`origin/main`,
  so it spuriously refuses — and silently leaves behind — merged branches whose
  upstream is gone under `deleteBranchOnMerge`, or when HEAD is a stale detached
  commit. The `merge-base --is-ancestor` probe has just proven containment,
  which is exactly the safety `-d` is meant to provide. Outside that probe,
  `-D` is unsafe.
- **Why the loop keys on exit codes.** The old `git branch -vv | awk '/: gone]/'`
  pipeline silently no-opped under rtk's output rewriting before v0.45.0 (see
  `reference_rtk_output_is_not_a_data_channel`). The merge-probe loop keys on
  exit status, not parsed stdout, which is why it stayed correct through that
  regression — and why it stays robust under any hook.
