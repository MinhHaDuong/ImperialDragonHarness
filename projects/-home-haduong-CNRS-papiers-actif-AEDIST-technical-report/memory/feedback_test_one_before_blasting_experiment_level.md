---
name: test-one-before-blasting-experiment-level
description: "The \"test one before blasting\" rule applies at experiment design too, not only per-call"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c5347cee-3d04-49c2-9690-24ae69b390aa
---

The project rule "Before any parallel batch of API calls: dry-run, 1
real call per regime, inspect, then full batch" (`.claude/rules/workflow.md`)
applies at the **experiment level**, not only at the per-API-call
level. An experiment of N reps × M models is itself a batch; running
1 × M first catches systemic failures (parser bugs, prompt failures,
API-shape surprises, refusals) before they multiply across N.

**Why:** verified in the SOTA frontier-API derisk pass (2026-05-20).
A pre-implementation N=1 stage would have caught the 0168 `include=`
directive gap and the 0173 `tools=[{type:web_search}]` client-side
function-call trap, each of which would have wasted ~$30 if discovered
at N=3.

**How to apply:** when designing any multi-condition experiment with
≥3 reps per condition, propose a single-rep smoke pass first. Frame
the N=1 stage as the project's own rule, not as added bureaucracy.
See [[phase-b0-n1-gate]] for the AEDIST instance.
