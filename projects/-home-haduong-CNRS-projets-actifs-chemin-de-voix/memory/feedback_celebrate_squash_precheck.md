---
name: celebrate-squash-precheck
description: /celebrate pre-check fails on squash-merged branches; verify via gh pr view + merge commit ancestry instead
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a35f7c24-d6a7-4938-99a5-8e7811affaeb
---

`/celebrate` pre-check runs `git merge-base --is-ancestor HEAD origin/master`. After a squash merge, HEAD is the last commit on the PR branch — this commit is NOT an ancestor of the squash commit on master. The check fails even though the PR is merged.

**Correct approach:**
1. `gh pr view N --json state,mergedAt` — confirms MERGED
2. `git merge-base --is-ancestor <squash-oid> origin/master` using the `mergeCommit.oid` from `gh pr view N --json mergeCommit`

**Why:** Squash merge rewrites history — the PR branch commits become a single new commit on master. `HEAD` on the PR branch has no ancestry relationship to that new commit.

**How to apply:** When the pre-check fails after a known-good merge, run the two-step verification above before proceeding with celebrate steps.
