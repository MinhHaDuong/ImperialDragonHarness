---
name: room-for-multilingual-embedders
description: "R7 (multilingual) is hard and C3's memory ceiling gives way — the budget adjusts to the measured embedder, never the reverse"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f3122769-3cbb-4fa8-9993-0e8d20249ebc
  modified: 2026-08-30T13:55:22.576Z
---

Author ruling 2026-08-29 (spec/DECISIONS.md): R7 multilingual is a hard
requirement; C3's steady-state memory ceiling gives way. Every multilingual
candidate measures above the old number, so memory is a **reported cost** that
sets the new ceiling (ticket 0268 re-pins C3 and R20's gate from the
measurement, in one commit) — never a rejection gate on candidates.

**Why:** On 2026-08-30, discussing X3a's at-rest figure (~132 MiB keyword-only
on trunk), I presented the old ≤ 300 MB budget as the envelope the embedder
must fit under ("~165 MiB headroom for the embedder"). The author corrected:
we agreed to *make room* for multilingual embedders. The arithmetic runs
measured keyword floor + chosen embedder's measured residency → proposed new
C3 value, not old budget − floor → allowed embedder size.

**How to apply:** The replacement landed 2026-08-30: C3 is ratified at
~750 MB server p95, derived from the recommended candidate's measured
residency plus idle, robust to every candidate measured (0268 closed; the
red-first agreement test keeps C3 and DESIGN §2.8 on one number). The durable
lesson survives the resolution: when a ruling has displaced a ceiling, never
argue headroom under the old number — the arithmetic runs measured floor +
chosen component → proposed ceiling, not old budget − floor → allowed
component size. Argue candidate selection on retrieval quality, cost, and
cross-lingual fit ([[registry-not-knobs]] carries the sibling ruling); report
memory honestly but never use it to disqualify or to frame "headroom" as a
constraint on the choice.
