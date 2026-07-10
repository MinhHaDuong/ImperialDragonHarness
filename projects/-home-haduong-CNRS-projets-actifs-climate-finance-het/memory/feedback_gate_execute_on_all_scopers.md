---
name: feedback_gate_execute_on_all_scopers
description: "Gate a raid's execute-launch on ALL scoping agents returning, not a quorum — a late scoper can surface a scope-narrowing finding that rewrites the ticket."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ffdf7ae-8403-47bc-87ed-e116676de228
---

In a raid, do not launch the Execute wave until **every** Phase-2/3 scoping agent
has returned. A slow scoper is often slow *because* the ticket is the hairy one —
exactly the plan most likely to be wrong.

**Why:** raid 2026-07-10. Three of four scopers returned; I said "all four scoped"
and launched all four executors. The fourth (0218) was still running and came back
with a **major** finding: the ticket undercounted its class 4-5x (sub-Makefile
`*_TABLES` dir-vars route ~70 more targets), and the naive generalized guard would
false-positive-storm. The 0218 executor ran without that correction and produced
nothing usable.

**How to apply:** Collect the full scoper set, read every drift/antipattern/scope
finding, THEN compose executor prompts (folding in each scoper's corrections). If
one scoper lags, wait for it or drop its ticket from the wave — never launch its
executor off the un-scoped ticket. Pairs with
[[feedback_agent_prompt_worktree_rooted_paths]] (the same 0218 run's second error).
Related: [[feedback_pilot_one_instance_critiques_the_ticket]].
