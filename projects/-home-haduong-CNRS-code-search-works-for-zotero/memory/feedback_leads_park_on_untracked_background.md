---
name: feedback-leads-park-on-untracked-background
description: Team-lead subagents park waiting on detached background runs the harness does not track; instruct chunked foreground calls up front
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e3539725-9ee4-4662-bd11-94fde1db9112
  modified: 2026-08-30T13:47:11.693Z
---

Three independent sonnet team-leads in one session (2026-08-30, the embedder
campaigns) launched their long sweep as a detached background process, then
stopped "waiting for the completion notification" — which can never arrive,
because a subagent's stop is reported when it has no live tracked children,
and a nohup'd process is not one. One lead re-parked twice, the second time
behind wait-loops that were themselves untracked.

**Why:** the harness re-invokes an agent when *tracked* background work
finishes; a detached process is invisible to it, so "wait for the
notification" deadlocks the lead while its compute runs on unowned.

**How to apply:** in every delegation prompt for long compute, state up
front: no detached processes, no wait loops, no monitors — drive the work as
chunked foreground calls the agent waits on (one model or rung per call,
under the tool timeout), relying on the harness's resumability to skip
completed cells. When a lead parks anyway, one resume message with those
literal instructions recovers it; on the second drift, take the work over
directly ([[feedback-executor-gate-loop-stall]]).
