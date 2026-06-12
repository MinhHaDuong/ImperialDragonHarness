---
name: project_coherence_axis_decomposition
description: Coherence quality dimension split into internal/external reference-free composites — ticket chain 0201→0396→0397
metadata: 
  node_type: memory
  type: project
  originSessionId: 1e1f7b67-8333-48ac-bcde-24257f653e12
---

The §2 "Coherence" quality dimension (tracked by [[project_three_quality_argument]] axis, ticket 0201) is being built bottom-up as reference-free indicators, designed with the author in an Imagine session (2026-06-03):

- **Per-field indicators** (diagnostic breakdown, ADR-7): `coherence_vocab_adherence`, `coherence_status_vocab_adherence`, `coherence_capacity_nonnegative` (PR #651), `coherence_row_atomicity` (1NF detector, ticket **0396**, merged on main).
- **Composite layer** (ticket **0397**, PR #668, `Blocked-by 0396`): two scores — `coherence_internal` (fuel/status vocab, 1NF-atomic, capacity≥0 — response only) and `coherence_external` (province∈gazetteer, **capacity≥30-and-numeric** — world knowledge, not gold).
- **Level dimension** (tickets **0401** schema+reference-derivation, **0402** model-emits-level+capacity-coherence `Blocked-by 0401`; PR #671): a `level` enum `{Unit, Block(CCGT-only), Plant, Complex, Unknown}` makes granularity first-class. Author decisions: Site=Complex, model assigns level, Plant="Site+number" / Complex=bare Site. Capacity plausibility is **level-conditional** (Unit coal≤1350/CCGT≤~900, Plant≤~3200, Complex any) — lives in 0402, NOT 0397.

Locked design choices:
- **Aggregation = per-row pass/fail** (row coherent iff passes ALL checks). Chosen because per-field signals correlate (a merged 1NF row also has doubled out-of-band capacity) — pass/fail counts the bad row once, avoids double-penalty. Composites are stricter than any per-field fraction (≈ product of pass rates). Keep per-field fractions as breakdown, never replace.
- **Objective = reference-free / production** (PyPSA-ASEAN, no gold). This is why a 1NF-violating row IS a defect here — the OPPOSITE reading from ticket 0393 (reference-based, where merged rows are decomposed and matched, fabricating nothing). Do not conflate the two objectives (see docs/inventory-1nf-handoff-exp2.md §Two objectives).
- Capacity: lower bound 30 = task-scope (prompt asked >30 MWe). A flat upper band was REJECTED after verification: operating centrales max ≈1500 MW (none >1600) but reference power-centers legitimately reach 6000 MW, so a flat ceiling mislabels ~25% of gold. Plausibility is level-conditional → handled by the Level dimension (0401/0402), not a constant. The capacity-vs-level signal catches power-centers (e.g. LNG Mỹ Giang 6000) whose NAME has no merge marker, which the 0396 verbal 1NF regex misses — complementary detectors.

Deferred: "confidence vs #sources" consistency check → v2 (data not emitted at extraction). Mart regen → 0387. Spider figure axis (one→two) → 0201.
