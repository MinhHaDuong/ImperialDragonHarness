---
name: project-reference-v2-adopted
description: Reference v2.1 (173 plants, extensions standalone) adopted 2026-06-06; v2 (170) history; never hardcode count
metadata: 
  node_type: memory
  type: project
  originSessionId: dd5fd1a6-54f6-4a9c-8dac-81a5fb68b497
---

Reference v2.1 adopted 2026-06-06 (PR #780, ticket 0445): **173 plants** — v2 (170, PR #767/0413) with the 4 extension rows standalone instead of absorbed-as-units (Uong Bi II vanished 1:1, its only row was its extension; Uong Bi I flips operating→retired 405→105 MW). Decision evidence: Exp2 net measurement (gate doc `data/reference/extensions_standalone_vs_absorbed.md`). Pinned snapshot is `raw/pipeline+extensions-as-plants-2026-06-05.ods` — a hand edit of the 2026-06-05 capture; **the master on the author's other machine does NOT carry the edit — ticket 0458 (needs-human) must replay it before any re-pin, else adoption silently reverts.** Status projection at load via `evaluate.project_status`. `evaluate.reference_plant_count()` is the canonical size — never hardcode 163/170/173 in render scripts (ratchet 0447; lying labels bit 4 scripts in one day). Deliberate v1-era leftovers: census tables/macros (their render recipes CRASH on the post-0422 mart — zero census rows — pre-existing), SC/verification mart rows + tab_self_consistency/tab_verification (deferral 0444).
