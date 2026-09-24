---
name: feedback_review_pr_fork_stops_before_synthesis
description: "The /review-pr fork returns \"waiting on the panel\" and never posts; its three perspective reports land in .panel/<pr>/ and the orchestrator synthesizes and posts the review by hand before merging (seen twice, 2026-09-22)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a12625da-f40d-43cd-8b7d-fd6f422a6920
  modified: 2026-09-22T10:33:10.018Z
---

On PRs #1444 and #1445 (2026-09-22, review:trivial label, one review cycle
required by the merge gate), `/review-pr` launched its three perspective
agents, armed a Monitor and a ten-minute deadline, then returned with
"Waiting on the panel notifications before synthesis and posting" and did
not resume when the agents finished. No review reached the PR; the merge
gate hook counted zero reviews.

**Why:** a forked skill that stops with live children is not re-invoked by
its children's completion in this runtime; the notifications reach the
parent session instead.

**How to apply:** after the three `task-notification`s (correctness,
consistency, doc-propagation) arrive, read the verdict lines in
`.panel/<pr>/*.md` in the session worktree, fix anything a perspective
flagged as blocking, post one `gh pr review --comment` with the roster
table and the dispositions, then merge. Do not relaunch `/review-pr`: it
spends another panel for the same reports. Full `/gaze` is unaffected (its
own orchestration posts). Related: [[feedback_worktree_guard_usr_bin_git]].
