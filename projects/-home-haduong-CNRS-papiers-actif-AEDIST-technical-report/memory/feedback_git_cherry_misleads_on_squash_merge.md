---
name: feedback-git-cherry-misleads-on-squash-merge
description: "`git cherry main <branch>` shows `+` (unmerged) for branches that were squash-merged — patch-IDs change. Verify via PR head-branch / merge-commit lookup instead."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aacff427-fd62-410d-9b06-5e233b752256
---

`git cherry main <branch>` works by comparing patch-IDs (computed from each commit's diff). For squash-merge: N source commits collapse into 1 commit on main whose patch-ID equals the *summed* diff, not any individual source commit's patch-ID. So `git cherry` reports all N source commits as `+` (unmerged) — even when the net diff is fully on main.

**Why:** During 2026-05-23 healthcheck cleanup I almost flagged three squash-merged worktrees (t0226-nemotron-calibration / t0224-stage7-consumer-dates / ticket-0231-mistral-dates) as "must salvage — real feature work never landed." User pushed back: "Check if t0226 was not squash-merged." It had been (PR #416 → `b98e4d9`); the classifier swap was on main; the three "unmerged" commits were just the pre-squash versions of work that already landed.

**How to apply:** When deciding whether a dead-agent worktree branch is safe to remove, do NOT trust `git cherry main <branch>` for branches that may have been squash-merged. Instead:

1. Query the PR head branch name: `gh pr view <N> --json headRefName,mergeCommit`.
2. If a merged PR's `headRefName` equals the branch name, the branch is squash-merged regardless of `git cherry` output.
3. Or scan main for the PR-number suffix: `git log main --grep="(#${PR})\b" --oneline`.

**Squash merge is now disabled (2026-05-25).** New PRs use regular merge commits — `git cherry` works correctly for them. This memory still applies to branches predating that date, where many PRs were squash-merged. When cleaning up old worktrees, still use the `gh pr view` probe above. Related: [[feedback-killed-agent-salvage]].
