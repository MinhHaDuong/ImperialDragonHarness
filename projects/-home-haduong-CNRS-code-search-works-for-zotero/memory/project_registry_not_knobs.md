---
name: project-registry-not-knobs
description: Author rulings 2026-08-29/30 — no per-axis embedder knobs; curated entries pin model+dtype+pooling+template+normalize; per-device optimal rung
metadata: 
  node_type: memory
  type: project
  originSessionId: e3539725-9ee4-4662-bd11-94fde1db9112
  modified: 2026-08-30T13:47:04.671Z
---

Author ruling 2026-08-29: no per-axis embedder knobs upstream — the ask is a
curated registry entry whose knob is its id. Ruled again in requirement form
2026-08-30: R30 (GPU acceleration is a requirement), C3 re-pinned at ~750 MB
p95 from the measured multilingual residency.

State as of 2026-08-30: the measurement train (tickets 0261–0266, 0481–0482)
is closed and merged. The recommendation (ticket 0267, PR #110) selects
multilingual-e5-base under a six-clause rule; the author is reading it. The
0440 upstream issue is drafted at `verification/ISSUE-DRAFT-0440.md`, ticket
closed on a recorded deferral — filing awaits his approval after #110, and it
is a fresh authorized outward action when it comes.

Two measured facts that shape any future entry design: the optimal rung is
per-device (no CUDA int8 matmul kernel, so fp32 is the fast GPU rung while
8-bit halves CPU RAM), and a broken (model, rung) pair drags RRF-fused
results below keyword-only — the strongest argument for pinning rungs inside
entries. Adopt-by-copy (embed on padme, retrieve on doudou) is held on
[[feedback-metric-decides-the-verdict]] grounds: ticket 0485 must price the
X8 0,999 bar on the task metric first.
