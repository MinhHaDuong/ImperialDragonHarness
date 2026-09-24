---
name: feedback-leads-park-on-untracked-background
description: Team-lead subagents park waiting on detached background runs the harness does not track; instruct chunked foreground calls up front
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e3539725-9ee4-4662-bd11-94fde1db9112
  modified: 2026-09-24T00:45:36.723Z
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

Recurred 2026-09-06 with a fable team-lead whose Zotero injection ran on a
remote host over ssh: it left "a background waiter" and stopped. Model tier
does not protect against it, and a remote process is exactly as untracked
as a local nohup. The prompt that launched it said nothing about waits; the
rule above has to be in the launch prompt, not only in the recovery message.

Recurred four times in the raid of 2026-09-23: the 0816 and 0823 executors
parked on their own `/review-pr` panels, the 0818 executor polled a 6-hour
clone run on padme, and a forked `/verify-gate` returned "still waiting" on a
`make check` it had started itself. What worked: stop the parked agent once
`git status` is clean and its head is pushed, and take the rest over — the
coordinator watches the remote run with a Monitor on its progress counters,
commissions one synchronous review whose brief bans background waits, and
re-runs the gate with the gates already quoted on the PR and "run nothing in
the background" in its args. The coordinator's own failure was symmetric:
waiting four hours on completion notices without measuring whether the
worktree was still moving.
