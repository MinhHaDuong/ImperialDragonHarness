---
name: smoke-one-then-blast-parallel
description: "Fan-out waves of independent external calls run one smoke first, then the REST IN PARALLEL — sequential-after-smoke wastes wall-clock"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d964c228-4677-46c7-9d95-af2b29bad4c0
---

Author correction on the 0207 audition wave (2026-07-14): the wave design
should have been "run one, then blast the rest in parallel" — I ordered
the three post-smoke candidates sequentially on a guessed free-tier
rate-limit risk.

**Why:** independent external calls (different model backends, separate
sandbox containers, no shared mutable state beyond an append-only log)
don't contend; sequential ordering after the smoke multiplies wall-clock
by N for no protection. The smoke is the only necessary serialization —
it validates the shared transport/prompt path. Rate-limit worry is
per-backend and handled by recording a DNF, not by serializing everyone.
The external-peer-review skill already codifies this exact shape
("smoke-test ONE combo first… run the rest in the background").

**How to apply:** when launching N independent runs against external
endpoints (auditions, peer-review combos, API sweeps): serialize only the
first as a smoke; on success, launch the remaining N-1 in parallel, each
fail-independent (one DNF never blocks siblings). Serialize beyond that
only on EVIDENCE of contention (same backend, shared quota actually
observed), and say so.
