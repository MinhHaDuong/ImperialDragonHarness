---
name: project-reference-v2-adopted
description: Reference grew v2.1(173)→v2.2(176)→v2.3(180); 180 is canonical now; manuscript still says 173 (STALE); never hardcode count
metadata: 
  node_type: memory
  type: project
  originSessionId: dd5fd1a6-54f6-4a9c-8dac-81a5fb68b497
---

Reference v2.1 adopted 2026-06-06 (PR #780, ticket 0445): **173 plants** — v2 (170, PR #767/0413) with the 4 extension rows standalone instead of absorbed-as-units (Uong Bi II vanished 1:1, its only row was its extension; Uong Bi I flips operating→retired 405→105 MW). Decision evidence: Exp2 net measurement (gate doc `data/reference/extensions_standalone_vs_absorbed.md`). Pinned snapshot is `raw/pipeline+extensions-as-plants-2026-06-05.ods` — a hand edit of the 2026-06-05 capture; **the master on the author's other machine does NOT carry the edit — ticket 0458 (needs-human) must replay it before any re-pin, else adoption silently reverts.** Status projection at load via `evaluate.project_status`. `evaluate.reference_plant_count()` is the canonical size — never hardcode 163/170/173/176/180 in render scripts (ratchet 0447; lying labels bit 4 scripts in one day).

**UPDATE 2026-06-09: the count has since grown past 173.** Evolution in `vietnam_thermal_plants_v2_classified.csv`: 170 (v2, 0413) → **173** (v2.1, 0445) → **176** (v2.2, 0472 Kiên Lương complex) → **180** (v2.3, 0395 +4 potential coal sites: Kim Sơn, Rạng Đông, Yên Hưng, Phú Thọ). **180 is canonical now** — `reference_plant_count()` returns 180, `tests/test_reference_count.py` asserts 180, all `N_REFERENCE_PLANTS` figure constants = 180. **BUT `slides/manuscript/main.md` still says "173" everywhere** (abstract, captions) — 0444 propagated 170→173 but nobody propagated 173→180 after 0472/0395. Open question (surfaced in 0486 dialogue): are Exp1–3 frozen at 173 for scoring, or does the manuscript need a 173→180 sweep + re-score? Likely its own ticket. See [[feedback-compute-before-figure]]. Deliberate v1-era leftovers: census tables/macros (their render recipes CRASH on the post-0422 mart — zero census rows — pre-existing), SC/verification mart rows + tab_self_consistency/tab_verification (deferral 0444).
