---
name: project-reference-fix1
description: "Reference dataset state — frozen v1 scores Exp1-3 with documented defects (fix1 was leapfrogged, never shipped); corrections flow through the master + regeneration pipeline 0420→0416→0419"
metadata: 
  node_type: memory
  type: project
  originSessionId: e2c43e27-0ba8-4697-8789-f99a8209cd45
---

`data/reference/vietnam_thermal_v1.csv` (frozen at `85a0e6c7`) scores Exp1–3
**as-is**. Its defects are documented in `PROVENANCE.md` § "Known defects of
v1" (DH2 romanization dup, Quảng Trị 1 "Unit 2, Unit 2" typo, Dong Nai
Formosa / Ha Tinh Formosa duplicated-name rows) with measured impact: FP
399→399, FN delta = 80 phantom misses — nil operationally. An interim patch
("fix1") was built, measured, then **leapfrogged** — never shipped (PR #699
final scope = documentation + `fp_audit_exp2.py --reference` instrumentation,
closes ticket 0394).

Corrections flow through the pipeline chain: **0420** (extract ODS→CSV from
`data/reference/raw/` snapshot of pipeline.ods; dtype=str; input validation:
unique names, "Unit" ⇒ Level=unit) → **0416** (aggregator rewrite; OUTPUT:
plant name = strictly UNIQUE key, same-name multi-status = error resolved in
the master; never synthesize names) → **0419** (consumers: one default-ref
config, `--reference` everywhere). Adoption = **0413** (after 0412 Cergy
archive); v1→v2 delta must match the PROVENANCE checklist. 0395 (add plants)
is blocked on the pipe.

**Why:** the plant-level CSV is DERIVED from unit-level data (pipeline.ods,
hors projet, the user's sound master) by `HDM_aggregate.py`, whose
`groupby(name, status, …)` has no guards — root cause of all three defects.
Spreadsheet round-trips also strip leading zeros (`ires_code` 0121→121)
silently. Patching downstream duplicates upstream truth — always fix the
master + regenerate ([[feedback-no-invented-names]]).

**Gotcha:** ticket IDs allocated by `erg new` on sibling branches can
collide on main (0418 did, renumbered → 0420); re-check IDs after merging.
