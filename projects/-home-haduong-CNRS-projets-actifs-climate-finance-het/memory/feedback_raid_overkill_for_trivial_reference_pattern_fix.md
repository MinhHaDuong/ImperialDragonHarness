---
name: feedback_raid_overkill_for_trivial_reference_pattern_fix
description: full raid/gaze multi-agent protocol is too heavy for a trivial fix that exactly mirrors an existing reference pattern — recognize and use a lighter path
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ed8cf9ba-c782-4b47-a8ad-5c7a038005a8
---

Don't run the full `/raid` → worktree-isolated execute agent → `/gaze` multi-agent
fan-out → merge cycle for a single ticket whose fix is a few lines and already has
an exact reference implementation elsewhere in the codebase (e.g. ticket 0265:
mirror a 3-line pattern already applied twice by ticket 0262). Measured cost on
raid 265, 2026-07-17: 26m50s for the trivial fix itself (14m15s execute agent +
12m35s `/gaze` verify+merge on a 7-line diff), then another 15m24s to run a
*second* full PR+`/gaze` cycle just to file two follow-up ticket *descriptions*
containing no code.

**Why:** raid/gaze's multi-agent overhead (worktree setup, TDD ceremony,
regression-harness golden regeneration, 5-stage review fan-out) is fixed cost
regardless of diff size — it does not degrade gracefully to trivial, exactly-known
changes. The user's reaction: "that's glacial."

**How to apply:**
- Filing ticket text with no code (like follow-up tickets from a sweep) never
  needs its own branch+PR+`/gaze` cycle — commit directly (or bundle into an
  already-open PR) per the existing "bundle follow-up tickets into the spawning
  PR" rule in `rules/workflow.md`; don't invent a second full merge-request cycle
  for it.
- For a single ticket whose fix is small AND has a named, verified reference
  implementation already in the tree (exact line-level pointer, not just
  "similar shape"), consider a direct edit + one lightweight review pass instead
  of the full worktree-isolated-agent + multi-stage-gaze protocol — or ask the
  user first whether they want the heavy protocol for something this size.
- The full raid/gaze protocol earns its cost on ambiguous, multi-file, or
  higher-risk changes — not on a verbatim port of an established pattern.
