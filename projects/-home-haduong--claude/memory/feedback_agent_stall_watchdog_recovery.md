---
name: agent-stall-watchdog-recovery
description: Background agents (opus coder AND a gaze fork) stalled on the 600s stream watchdog in one night; liveness probe + salvage/finisher or supervisor-driven fix round recovers without losing work
metadata:
  type: feedback
---

2026-07-11 nightbeat: two independent background stalls in one run — an opus
execute agent (ticket 0284) killed by the 600s stream watchdog mid-edit, and a
/gaze fork on PR #496 that died silently after its simplify phase (worktree
left behind, no verdict, no error). Intermittent LAN-to-github outages the same
night likely contributed.

**Why:** watchdog kills leave salvageable state; a dead forked skill is
indistinguishable from a slow one without a liveness probe. A relay agent
watching a forked skill detaches when the fork backgrounds itself — its
"still running" report is not evidence of progress.

**How to apply:**
- Liveness probe for a silent fork: branch tip unchanged + no file mtime under
  its worktree for ~10 min + no verdict comment = dead, not slow.
- Stalled coder: `scripts/worktree-salvage.sh <wt>` then relaunch a finisher on
  the EXISTING branch (`git switch`, not `-c`) with push-retry loops for flaky
  network; record a `bump circuit-breaker` line in the ticket log.
- Dead gaze fork after its review posted: don't rerun the whole gaze — drive
  the fix round yourself, then run /verify-gate directly; remove the stale
  /tmp/review-N worktree only after confirming it is clean and pushed.

Related: [[feedback_verify_fork_under_execution]], [[feedback_rogue_agent_pattern]].
