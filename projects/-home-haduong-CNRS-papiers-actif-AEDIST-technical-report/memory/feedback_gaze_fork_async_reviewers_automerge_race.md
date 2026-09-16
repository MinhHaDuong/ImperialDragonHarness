---
name: feedback-gaze-fork-async-reviewers-automerge-race
description: gaze fork can return mid-flight with reviewers still running; queueing auto-merge before all reviewer reports arrive let a blocker land post-merge
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cc512206-ffe1-4383-923d-0af8b9ddbbce
---

During raid 539 (2026-06-11, PR #983): the /gaze fork returned while its three
reviewer agents were still running; their task-notifications arrived later,
directly to the orchestrator. A standalone /verify-gate APPROVED on partial
information, erg-pr-merge queued auto-merge, and the PR landed ~1 min before
the built-in-review and prose-panel reports delivered TWO real blockers
(both provenance claims contradicted by archived run records). Required a
fix-forward PR (#986).

**Why:** auto-merge converts "verdict now, reviews later" into "merge now,
blockers later". The gate saw zero review comments because the reviewers
hadn't posted yet — absence of findings ≠ reviews complete.

**How to apply:** when /gaze returns mid-flight ("reviewers launched,
waiting"), do NOT proceed to verify-gate/merge until all three reviewer
notifications have arrived (or their tasks show completed). If a merge must
be queued earlier, hold off `gh pr merge --auto` / erg-pr-merge until the
reviewer count is complete. Related: [[feedback-async-agent-continuation]].
Post-merge blocker recovery: fix-forward PR with `Ticket: none`, gate it,
rebase, merge — worked cleanly here.
