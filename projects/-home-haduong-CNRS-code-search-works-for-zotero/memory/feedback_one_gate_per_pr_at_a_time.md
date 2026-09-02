---
name: one-gate-per-pr-at-a-time
description: "Two review forks gating the same PR produce a contradictory public record; a lead's own /gaze plus an orchestrator-launched gate on one branch cost a four-comment tangle and an ESCALATE (PR 184, 2026-09-02)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ee96a039-b8bf-4fbf-ba29-dfc1c1507351
  modified: 2026-09-02T11:45:53.003Z
---

On PR #184 (ticket 0489, 2026-09-02) the team lead ran /gaze on its own PR while a
sibling gaze fork also fired on the same branch. Result within thirteen minutes:
an APPROVED comment (11:27), a REROLL comment (11:36) calling the first
"fabricated", a ticket log line repeating the accusation, a "correction" comment
from the branch owner, and a round-2 panel that escalated for human arbitration.
Every seat agreed the code was clean; only the record was broken. The timestamps
refuted the "fabricated" claim: the first verdict existed, it was simply
superseded. A sibling lead named the mechanism: nothing makes a gate's identity
legible to the next gate, so a second fork reads a first fork's legitimate
verdict as an impostor (same family as the fork-mistakes-itself-for-coordinator
failure, ticket 0551).

A second mechanism compounded it: the `review-184` worktree could not be
created under the session's isolation guard, so every gaze fork on that PR fell
back into the lead's own worktree, and one actor's uncommitted log line surfaced
under another reviewer mid-check. A gate launched from inside a lead's tree is
not isolated from the lead.

**Why:** a gate is a claim about the branch at one tip. Two claimants on one tip
with no shared roster cannot reconcile, and each "corrects" the other in public,
append-only, forever.

**How to apply:** one gate per PR at a time. When delegating a lane that ends in
/gaze, the orchestrator never launches its own gate on that branch while the
lead lives; when taking over a stalled gate, tell the lead first and wait for
its ack. On a contradictory record, do not adjudicate which verdict "wins":
have the branch owner write one log line stating the objective timeline with
comment timestamps, reduce the PR body's review history to a pointer at the
ticket log, then request one fresh gate on the tip. Related:
[[reconcile-seats-against-synthesis]], [[executor-gate-loop-stall]].
