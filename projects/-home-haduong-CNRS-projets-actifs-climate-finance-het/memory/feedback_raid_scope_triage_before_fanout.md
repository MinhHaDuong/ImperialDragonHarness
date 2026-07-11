---
name: feedback_raid_scope_triage_before_fanout
description: "A /raid over N tickets is not automatically an N-wide fan-out; triage for chains, shared-subtree conflict, and data-heavy gates first"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d329f489-e346-4cba-8c47-36d92cd64019
---

A `/raid A B C D` invocation names the *candidate* set, not the concurrency. Before
launching execute agents, triage the set and degrade the wave to the
autonomously-safe subset:

1. **Dependency edges** — a `Blocked-by` between two named tickets makes them a
   chain, not a parallel wave. The blocked child cannot start this session.
2. **Shared-subtree conflict** — if several tickets rewrite the same tree, parallel
   worktree agents collide catastrophically. A 173-file move that repoints imports
   across the repo (`utils` imported 169×) conflicts with every sibling that touches
   `scripts/`; running them together loses work at merge.
3. **Data-heavy / long-running exit gate** — a ticket whose gate is `make clean &&
   make all` (full data build) or a 173-file move exceeds the 10-min execute-agent
   timeout AND violates the no-long-running-build preference
   ([[feedback_no_long_running]]). Hold it for a supervised run; don't feed it to a
   background agent.

**Why:** fanning out the literal N would have launched four conflicting agents on
one subtree with a doomed 173-file/make-all agent among them — a costly failure the
invocation's surface (four ticket IDs) hides.

**How to apply:** verify the tree cheaply (file count, import fan-in, whether the
target script even has a Make target), state the wave restructure, and ask the author
only the one call that's genuinely theirs (run the heavy ticket now vs hold). Then run
the safe subset. Concretely (raid 240/241/242/248, 2026-07-11): held 0240 (173-file
move + make all) and 0241 (blocked-by 0240); ran only 0248 (tests-only) + 0242
(one-file sever) as two parallel agents on disjoint files — both merged clean.

Pairs with [[feedback_pilot_one_instance_critiques_the_ticket]] (the same pass that
sizes the raid also falsifies a ticket's guessed approach — 0242's "extract a label
helper" was wrong; the real coupling was two live plotter calls) and
[[feedback_gate_execute_on_all_scopers]].
