---
name: stacked-pr-waves-same-file
description: "Raid waves that edit the same file go out as stacked PRs (base = previous wave's branch); rebase the whole stack at every gate because the author lands decisions mid-raid"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bf0085d4-46ef-4004-9821-192ab96bca31
---

When a raid's tickets all edit the same file (e.g. `slides/manuscript/main.md`) and earlier waves are human-gated (needs-human, author-confirms-facts), run waves as STACKED PRs: wave N+1 branches off wave N's branch and its PR sets `--base` to wave N's branch. Each PR shows only its own diff; GitHub auto-retargets the next PR to main when its base PR merges (deleteBranchOnMerge).

**Why:** Raid 532-534 (2026-06-11). Three manuscript tickets, two human-gated. Independent branches off main would have produced merge conflicts for the author to resolve; the stack kept every diff surgical and the merge order (#964→#967→#968) trivially safe.

**How to apply:**
- Branch wave N+1 with `git switch -c tNNN origin/t<prev>`; PR with `gh pr create --base t<prev>`.
- The author works WHILE the raid runs: they may merge a wave PR after their own edits (PR #964 got author commits before merge) or drop a new directive brief into the ticket body on main. So `git fetch` + rebase the remaining stack at EVERY gate; treat ticket-log conflicts (both sides append log lines) as normal — resolve chronologically, keep both.
- After any amend to a lower branch, rebase the upper ones with `git rebase --onto origin/t<lower> <old-lower-tip> t<upper>` and `push --force-with-lease`; re-run the pinned-prose adherence tests, which are the fast composition check.
- A branch checked out in a finished agent's worktree can't be checked out elsewhere; do follow-up commits with `git -C <that-worktree>` (or run the fix agent in that worktree) instead of fighting git.

Related: [[feedback_rebase_drop_cascade]], [[feedback_gaze_fork_dies_in_background_jobs]].
