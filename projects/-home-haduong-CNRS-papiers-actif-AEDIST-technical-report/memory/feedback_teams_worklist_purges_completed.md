---
name: feedback_teams_worklist_purges_completed
description: "Teams shared worklist purges completed tasks — collect results from agent return values, not the worklist"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

The experimental Agent Teams shared worklist (`TaskCreate`/`TaskList`/`TaskUpdate`/`TaskGet`, enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) **is genuinely shared** between the lead and `Agent`-tool–spawned teammates (a sentinel task round-tripped: a read-only teammate echoed the lead's task back verbatim). Per-agent model tiering via the `Agent` `model` param works (haiku/sonnet/opus per task).

**But completed tasks are purged from the store** — once a teammate marks a task `completed`, `TaskGet` returns "not found" and `TaskList` omits it. So the worklist is good for *distribution* and a *live board*, NOT for durable result storage.

**Why:** 2026-06-14, verifier-team run on ticket 0578 (verify 42 reading-2 findings against `main.tex`). Lead-created task #1 vanished after a teammate completed it; only a second sentinel probe distinguished "completed-tasks-purged" from "worklist-not-shared".

**How to apply:**
- Have each teammate return its result as its **final message** (the lead collects from return values); never write a verdict into a task expecting to read it back.
- **Smoke-test one task** before fanning out — this is what surfaced the purge before it bit all 42 ([[feedback_autonomous_means_execute]]-style: test one before blasting).
- If model-sizing per item matters, **pre-assign batches by tier** rather than relying on dynamic claiming (claiming is first-come, so a haiku teammate could grab a judgment task).
- Respect the 8-concurrent-agent cap: batch N findings into ≤8 tier-pinned teammates.
