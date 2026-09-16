---
name: single-seed-determinism-blind
description: A determinism test that pins one PYTHONHASHSEED is structurally blind to hash-order defects — run the producer under two different seeds and compare bytes
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1d4ec5dd-d317-4e39-9063-f4754471e26c
  modified: 2026-07-28T14:52:43.522Z
---

A byte-compare determinism test run under a single pinned `PYTHONHASHSEED` (or with the seed pinned in the Makefile) passes even when the artifact depends on set-iteration order — the very defect it exists to catch. So did `test_determinism.py` and `make determinism-check` here, for months.

**Why:** pinning the seed makes runs identical to each other while both remain wrong; the defect only shows across *different* seeds. Sort-stability variants hide the same class: `sorted(set_items, key=...)` with ties falls through to hash order and reads as already-deterministic in review.

**How to apply:** any test of "producer X is deterministic" must run X twice under two *different* `PYTHONHASHSEED` values and `cmp` the outputs (see `tests/test_hash_seed_determinism.py`, ticket 0591 / PR #1272). When fixing one `list(set(...))`, sweep for the class including the tie-break variant (`nlargest`, stable sorts on tied keys) — it put a hash-seed-dependent journal list into the manuscript's venue table ([[assert-on-written-artifact]]).
