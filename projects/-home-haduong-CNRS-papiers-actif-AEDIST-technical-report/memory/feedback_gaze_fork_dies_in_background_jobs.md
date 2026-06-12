---
name: gaze-fork-dies-in-background-jobs
description: /gaze forked execution returns prematurely in background-job sessions — its background reviewer agents die with the fork; run reviewers + /verify-gate directly instead
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2797e83f-e20f-4229-85cb-4740dca5f4f9
---

In a background-job session (raid, 2026-06-11), `/gaze <PR>` twice returned
"completed (forked execution)" immediately after *launching* its three
reviewers, never awaiting them. The fork's background agents do not survive
the fork's exit: no verdict, no PR comment, no tasks in TaskList.

**Why:** a forked skill that launches `run_in_background` agents and then
ends its turn has no parent loop to receive the completion notifications;
the children evaporate. Interactive sessions don't hit this because the fork
stays alive.

**How to apply:** in autonomous/background sessions, don't call `/gaze`.
Substitute: launch the review agents yourself as awaited (foreground) Agent
calls — correctness reviewer + adherence/scope reviewer, `model: sonnet`,
read-only — fix all findings, then call `/verify-gate <PR>` (which forks but
completes synchronously and posts its verdict). This reproduced the full
gaze pipeline successfully for PRs #949/#955/#960. Confirmed again in the
2026-06-11 raid (PRs #958/#959): subagents wrapping `/gaze` left no durable
verify-gate comment on #958 even though the execute agent reported
"APPROVED by gaze" — treat such claims as hearsay until a verdict comment
exists on the PR; a sonnet subagent invoking `/verify-gate` directly
produced the durable verdict. Fix the skill itself in
the ImperialDragonHarness repo ([[claude-dir-is-idh]]): gaze must await its
reviewers before returning when forked.
