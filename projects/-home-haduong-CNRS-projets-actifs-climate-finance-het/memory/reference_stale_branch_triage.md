---
name: reference_stale_branch_triage
description: "How to judge an unmerged branch safe to delete when the ancestry probe fails — cherry, PR state, deleted files, refs/pull survive"
metadata:
  node_type: memory
  type: reference
  originSessionId: b3a3f237-89fa-41c5-b207-8bd99d3dcfe6
  modified: 2026-09-30T07:28:08.847Z
---

A branch that is not an ancestor of `origin/main` is usually still dead here.
The 2026-09-30 sweep deleted 21 such branches and lost nothing. The
discriminators, cheapest first:

- `git cherry -v origin/main <b>`: `-` means the patch is on main (rebased or
  cherry-picked); a `+` is often a pre-rebase copy whose counterpart has the
  same subject in the merged PR's commit list (`gh pr view N --json commits`).
- `gh pr list --state all --head <b>`: a closed PR's last comment names its
  successor ("superseded by #N") or the author's decision to drop it.
- `git cat-file -e origin/main:<path>` on every path the `+` commits touch: a
  fix to files main has since deleted cannot land (t1479 vs 0878).
- A PR's commits survive branch deletion at `refs/pull/<N>/head` on GitHub, so
  "branch kept for reference" is redundant once a PR exists (cut-pass-0274).

What a triage must still catch: a `+` commit that records an author decision
never carried to main. `t0870-integration-testing` held the 1501 scope
decision (59 of 392) while main's open ticket said "20 of the 115"; it was
carried over in PR #1589 before the branch went.

Not stale: `gh-pages` (the live observatory site; rule in `.claude/rules/git.md`).
A finished journal's `submission/*` branch becomes tags (`docs/revision-runbook.md`);
the pre-push hook blocks its deletion, bypassed once with `--no-verify` on the
author's go-ahead. Related: [[reference_branch_cleanup_incidents]],
[[feedback_diff_fully_before_deleting_a_fork]].

Run a branch/worktree audit from the primary checkout, not an `explore-*`
worktree: the isolation guard refuses any git naming another worktree (and the
rtk rewrite trips it too), so the audit stalls. Use `/usr/bin/git -C <primary>`
and a script file for loops. A `.claude/worktrees/<name>` dir with no `.git`
is a husk `worktree-gc` reports but never removes; `rm -rf` needs the author.
