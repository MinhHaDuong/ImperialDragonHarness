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

**State moves faster than this file.** The rulings above are durable; the queue position is not. As of 2026-09-02 twelve further rulings landed in one day, several of them on this axis (device selection needs positive usability evidence, X1 waits for its 650k substrate, stored attributes get their own filter path). Read `DECISIONS.md` for what is settled and `erg ready` for what is next; do not quote a ticket state from here.

Two measured facts that shape any future entry design: the optimal rung is
per-device (no CUDA int8 matmul kernel, so fp32 is the fast GPU rung while
8-bit halves CPU RAM), and a broken (model, rung) pair drags RRF-fused
results below keyword-only — the strongest argument for pinning rungs inside
entries. Adopt-by-copy (embed on padme, retrieve on doudou) is held on
[[feedback-metric-decides-the-verdict]] grounds: ticket 0485 must price the
X8 0,999 bar on the task metric first.
