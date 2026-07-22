---
name: feedback-sibling-close-collides-on-shared-blocker
description: "Parallel sibling PR merges collide on a shared dependent ticket's Blocked-by bookkeeping; pre-merge origin/main into each next sibling before erg-pr-merge"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f373ecb2-3c53-46ca-b0dc-a85ae6153cb5
  modified: 2026-07-22T12:38:24.382Z
---

In a multi-PR wave whose tickets all appear in one dependent ticket's
`Blocked-by:` list (e.g. R&R children of response-letter ticket 0283), each
`erg-pr-merge` close commit edits that shared ticket (removes its Blocked-by
line, appends a log line). Sibling closes therefore conflict even when the
PRs' own file sets are fully disjoint — an integration review checking only
the PR diffs will report COMPOSE-CLEAN and miss it (raid 284/285/282,
2026-07-22: #1080 bounced with "merge conflicts" after #1079 landed).

**Why:** the conflict is created *at close time* by erg-pr-merge, not by the
branches themselves, so no pre-merge diff scan can see it.

**How to apply:** after each sibling merges, `git fetch origin && git merge
origin/main --no-edit` into the NEXT sibling's branch (in its own worktree)
*before* running erg-pr-merge — the close commit then applies on a current
base. If a bounce already happened: resolve the shared ticket by union (keep
both close log lines chronologically, drop both Blocked-by lines), `erg
validate`, commit, push; on retry erg-pr-merge may bounce "close-claimed
ticket absent" because the first run already closed+archived — finish with
`gh pr merge <N> --merge` per the standing recovery recipe. Related:
[[feedback_fetch_before_sibling_merge]].
