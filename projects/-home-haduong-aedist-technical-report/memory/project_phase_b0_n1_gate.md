---
name: phase-b0-n1-gate
description: "SOTA 4-agent experiment runs Phase B as N=1 smoke first, gating N=3 on review"
metadata: 
  node_type: memory
  type: project
  originSessionId: c5347cee-3d04-49c2-9690-24ae69b390aa
---

The 4-agent SOTA frontier-API experiment (umbrella ticket 0166) runs
Phase B in two stages: **Phase B-0** (N=1, one rep per model = 4
outputs total) gates **Phase B** (N=3, full triple-rep dataset).
N=1 surfaces parser bugs, prompt failures, model refusals, and real
per-call cost at one-third the budget. N=1 cannot stand in for
variance analysis — claims of the form "model X is consistently
better than Y" still require the post-Phase-B N=3 dataset.

**Why:** decided 2026-05-20 after the Wave-2 derisk pass. Budget on
0166 splits accordingly: Phase B-0 ≤ $40, incremental Phase B ≤ $80,
total cap ~$140 unchanged.

**How to apply:** if asked to launch Phase B (N=3) without an
explicit Phase B-0 review pass on record, stop and ask for the
review first. Gate criteria for B-0 → B promotion: (i) all 4 adapters
produced valid RunRecords, (ii) parsed tables non-empty, (iii) costs
match the ≤$10/call budget empirically. See [[test-one-before-blasting-experiment-level]]
for the general principle.
