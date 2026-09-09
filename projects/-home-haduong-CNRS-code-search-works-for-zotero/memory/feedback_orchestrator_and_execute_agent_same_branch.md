---
name: feedback-orchestrator-and-execute-agent-same-branch
description: "A raid orchestrator that edits files directly on a ticket while its own dispatched execute agent is still pushing to the same PR branch creates a real ping-pong risk — stop the agent first, then reconcile by rebase"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1fdebb29-23af-4c69-80a0-fcb348964f4f
  modified: 2026-09-04T07:35:23.638Z
---

When a raid orchestrator, reacting to fresh review findings, starts
editing source directly on a PR branch that has an execute agent still
actively running (dispatched earlier for that same ticket), both sides can
push independent fixes to the same branch concurrently — the exact
same-file-same-branch ping-pong the raid circuit breaker is meant to
catch, just with the orchestrator itself as one of the two writers.

**Why:** on ticket 0638, a red-team review finding arrived while the
dispatched execute agent was still running and had already pushed two of
its own follow-up commits addressing *different* review findings on the
same files. The orchestrator started a local redesign without first
checking `git log`/`git fetch` against the remote branch, and only
discovered the divergence when a push attempt (implicitly, via a later
rebase) surfaced two unknown commits. Recovery required: message the
execute agent to stand down immediately (no further pushes/fetches/merges
from its side), then `git fetch` + rebase the orchestrator's own WIP onto
the agent's commits, manually merging each conflict by keeping the best of
both changes rather than discarding either side wholesale — one of the
agent's commits (raise → refused-Posture, for cleaner fail-closed
diagnostics) was a genuine, orthogonal improvement worth keeping inside
the orchestrator's larger redesign.

**How to apply:** before making any direct edit to a ticket's source files
while its execute agent might still be alive, first check whether that
agent is still running (`ListAgents`) and `git fetch` the branch. If the
agent is running, message it to stand down *before* committing local
changes, not after. When reconciling, prefer a rebase + per-conflict merge
over a blind force-push of either side — an agent's own fix for a
different finding is real work, not noise to overwrite.
