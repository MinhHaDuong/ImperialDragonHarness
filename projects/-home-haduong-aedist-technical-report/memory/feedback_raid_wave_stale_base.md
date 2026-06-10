---
name: feedback-raid-wave-stale-base
description: "a dependent raid-wave agent must branch from origin/main AFTER the dependency merges, or it silently reverts it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96516ff3-e9dd-43d9-94cc-9744a7da7120
---

Raid 2026-06-10: after merging 0511 (#924) into origin/main, I launched the
0512 execute agent with `isolation:"worktree"`. Its worktree based off **stale
local main** (`839cf157`, pre-0511) — not origin/main-with-0511 — so the 0512
branch never contained 0511's content. The heavy 0512 restructure of `main.md`
therefore *dropped* every 0511 fix (ρ caveat, 16/14/12 cohort counts, the
Wikipedia revision-902510278 provenance) and *re-introduced* the cost-savings
claim 0511 had cut. Merging 0512 as-is would have silently reverted 0511. Caught
only because a second (redundant) agent diffed against origin/main and flagged
the regressions.

**Why:** worktree `baseRef` can resolve to local HEAD, and a just-merged PR
isn't in local main until you pull it. In a dependency-ordered wave, "branch
fresh" is not enough — fresh-from-*what* matters.

**How to apply:** before launching wave N+1's agent, after merging wave N,
**confirm the new worktree branch actually contains the dependency commit**:
`git merge-base --is-ancestor <dep-merge-sha> <new-branch>` must pass. If not,
rebase the branch onto current origin/main before any content work. The cheap
fix is `git fetch && git -C <primary> pull` (or branch explicitly from
`origin/main`) right after each wave merge. Recovery when it has already
diverged: merge origin/main in and reconcile with the dependency's adherence
test as the objective anchor that its content survived. Related:
[[feedback_branch_from_stale_local_main]], [[feedback_rebase_drop_cascade]],
[[feedback_api_merge_fetch_after]].
