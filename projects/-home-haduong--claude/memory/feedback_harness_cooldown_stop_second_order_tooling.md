---
name: harness-cooldown-stop-second-order-tooling
description: "Author is done with second-order harness work (2026-07-14) — stop filing low-severity residual tickets, prefer deleting guards to patching them, point throughput at science projects"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 305eab50-40bb-476c-bed1-850c81a6cf07
---

On 2026-07-14 the author said: "I am tired of working on the tool, nitpicking,
fixing the fixes to imaginary problems, and fighting the system." The data
backed it: the open queue was 100% second-order harness tickets (guards about
guards, residuals of residuals), ~20% of all tickets ever filed were guard +
worktree mechanics, and severity had decayed to nice-to-haves.

**Why:** The sweep-and-file machinery ([[feedback_batch_decisions_run_to_end]]
era rules like "sweep results are decisions") turned every finding into a
ticket, producing an equilibrium backlog that consumed raid throughput on
itself. [[feedback_harness_is_the_deliverable]] no longer licenses unlimited
tooling churn — the harness at equilibrium is done; it exists to produce
papers.

**How to apply:**
- File a harness ticket only if the defect blocks a merge, corrupts state, or
  bites a science project (chemin-de-voix, AEDIST, papers). Below that bar:
  fix inline, note in memory, or drop.
- Sweeps (molt, healthcheck, skill-doctor, roar residuals) report; they do not
  mint low-severity tickets.
- When a guard misfires, ask first whether its defect class has fired
  recently; prefer deleting the guard (and its tests) over patching it.
- Default raid/autonomous throughput toward the science repos, not the harness
  queue.
