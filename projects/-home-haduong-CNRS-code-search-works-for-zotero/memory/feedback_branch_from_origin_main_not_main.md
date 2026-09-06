---
name: feedback_branch_from_origin_main_not_main
description: "In a worktree session local main goes stale silently; branch from origin/main, and let a gate's own domain count catch it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 23ae8345-4e0c-469c-8519-4d269f82e902
  modified: 2026-09-03T16:07:11.988Z
---

`git switch -c <new> main` in a worktree session branches from a **stale**
local `main`. Fetching updates `origin/main`; nothing updates `main` unless
something merges into it, and a long session merging via the forge never does.

**Why:** on 2026-09-03 a branch cut this way carried a tree from before four
merges. Nothing about the checkout looked wrong — clean status, tests green,
628 passed. What exposed it was `check_progress.py` printing **24 requirements**
where main had 23: a domain invariant the gate recomputes, disagreeing with what
the session knew to be true. A generic gate would have stayed green, because the
old tree was internally consistent — it was consistent with the wrong world.

**How to apply:** always `git switch -c <new> origin/main` after a fetch. And
read a gate's *content* line, not just its exit code: the number in
"23 requirements over 5 goals" is the kind of assertion that catches a stale
base, a wrong worktree, or a lost merge, none of which a pass/fail can see.
Related: [[feedback_stage_by_path_in_shared_checkouts]],
[[feedback_green_prs_red_union]] — after merging a wave, re-run the gate on
`origin/main` itself, since each PR was green against a base that has moved.

**Second instance, 2026-09-03 (same repo, same day, worse drift):** an
end-of-day `/lair` housekeeping pass found the primary checkout's local `main`
42 commits behind `origin/main` — last synced at PR #299, hours earlier — with
nothing ever prompting a sync in between. This drift was caught by a different
domain-count signal than the first instance: `molt`'s branch-hygiene sweep
(`git merge-base --is-ancestor <branch> main`) reported dozens of long-since-merged
branches as "unmerged," because "unmerged into stale local main" and "unmerged
into origin/main" are different questions the tooling doesn't distinguish by
name. Any branch-hygiene or merge-base check inherits this trap, not just
`check_progress.py`'s requirement count — fast-forward local `main` from
`origin/main` by ref (`git fetch origin main:main`, or
`scripts/sync-local-main.sh`) before trusting *any* ancestry-based check, not
only before cutting a new branch.
