---
name: feedback_no_rebase_when_force_push_denied
description: "When the session denies force-push, do NOT rebase a pushed PR branch before merge — merge as-is; the rebase strands local ahead of remote and breaks erg-pr-merge's non-idempotent close+push"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 12e5b0a9-df08-49c1-a87a-fbee972ce165
---

git.md says "rebase at every gate," but that assumes force-push is available.
When the session **denies `git push --force-with-lease`** (a common guard in
this harness), do NOT rebase a branch whose PR is already pushed and mergeable.

**Why:** rebasing rewrites the branch's commit SHAs, so local diverges from
`origin/<branch>`. You then can't force-push the rewrite. Worse, `erg-pr-merge`
next runs its non-idempotent step — `erg close` commits the ticket archive on
top of your *local* (rewritten) branch and tries a plain `git push`, which is
rejected non-fast-forward. Now the ticket is closed+archived locally but the
close commit is not on the remote, and re-running `erg-pr-merge` fails
("no ticket found"). Recovery: `git checkout <origin-branch-tip>` (detached),
`git cherry-pick <close-commit>`, ff-push, then `gh pr merge --merge` directly
(raid 234/235, 2026-07-10, PR #998).

**How to apply:** the rebase's only benefit is currency, which verify-gate
reports as a non-blocking *nit*. If `mergeStateStatus` is CLEAN and the base is
conflict-free (parallel work landed in different files), skip the rebase and let
`erg-pr-merge` / the GitHub API merge as-is with a merge commit. Only when the
bases genuinely conflict do you need to integrate — and then `git merge
origin/main` into the branch (not rebase), which keeps local == remote after a
normal push. See [[feedback_force_push_denied_rebuild_clean]] and
[[feedback_fetch_before_sibling_merge]].
