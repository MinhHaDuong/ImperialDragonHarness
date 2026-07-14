---
name: agent-stall-watchdog-recovery
description: Background agents (an opus coder AND a gaze fork) stalled in one night; both recovery paths are codified — gaze fork in skills/gaze/SKILL.md § Fork execution contract "Fork liveness", stalled coder in skills/raid/SKILL.md § Circuit breakers; entry keeps only what the skills don't state
metadata:
  type: feedback
---

2026-07-11 nightbeat: two independent background stalls in one run — an opus
execute agent (ticket 0284) killed by the 600s stream watchdog mid-edit, and a
/gaze fork on PR #496 that died silently after its simplify phase (worktree
left behind, no verdict, no error). Intermittent LAN-to-GitHub outages the same
night likely contributed.

**Gaze-fork stall detection and recovery is now codified** in
`skills/gaze/SKILL.md` § Fork execution contract, "Fork liveness" clause
(`fork_liveness_seconds` / `GAZE_LIVENESS_WINDOW_S`). Follow the skill, not
this entry, for that path.

**Stalled-coder recovery is codified too**, in `skills/raid/SKILL.md`
§ Circuit breakers ("Killing a mid-execution agent — salvage WIP first" and
"Agent timeout"): salvage via `scripts/worktree-salvage.sh`, relaunch the
finisher on the EXISTING branch (`git switch`, not `-c`). What raid does not
capture: wrap the relaunch's pushes in retry loops on a flaky network, and
the 600s stream watchdog can kill a coder well before raid's 10-minute
no-push breaker would fire.

**Cross-cutting lesson gaze's contract doesn't state generally:** a relay
agent watching any forked skill detaches when the fork backgrounds itself —
its "still running" report is not evidence of progress, for gaze or any other
forked skill.

Related: [[feedback_verify_fork_under_execution]], [[feedback_rogue_agent_pattern]].
