---
name: feedback-pipeline-presentation-overlays-raids
description: When presenting a ticket pipeline, overlay what parallel instances are raiding — worktrees, branches, open PRs — so claimed tickets aren't shown as available
metadata:
  type: feedback
---

When asked to present the ticket pipeline, the `erg ready`/`erg list` view is
incomplete: overlay live parallel-instance activity before calling a ticket
available (author directive, 2026-07-14).

**Why:** a ticket can be "ready" in the DAG while a raid worktree or open PR
has already claimed it; presenting it as free invites a duplicate claim —
the same optimistic-allocation trap as ticket IDs.

**How to apply:** after the erg queries, in the same pass run
`git worktree list` (raid-N-M and tN-* names encode claims), scan branch
names and open merge requests for ticket IDs, and check worktree recency
(mtime, commits ahead, dirty state) to separate live claims from stale
leftovers. Report three lanes: ready-and-unclaimed, claimed-in-flight,
blocked/parked. Related: [[feedback_shared_worktree_live_session_contention]].
