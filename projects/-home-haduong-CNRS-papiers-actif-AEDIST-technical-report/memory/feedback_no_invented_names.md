---
name: feedback-no-invented-names
description: "Never invent a project/plant name in the scientific reference — names must be source-attested; disambiguate structurally (status, units), not nominally"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2c43e27-0ba8-4697-8789-f99a8209cd45
---

The user rejected PR #699's first version for renaming two reference rows
`Dong Nai Formosa extension` / `Ha Tinh Formosa ... extension`: "Il n'est pas
permis d'inventer un nom de projet." Existing `... Extension` rows are
legitimate only because the sources name them that way (mở rộng in the PDPs).

**Why:** the reference is a registry of real-world assets with provenance
discipline (PROVENANCE.md); a synthesized designation is a fabrication, even
when convenient for making a key unique.

**How to apply:** when two reference rows legitimately share a name (e.g.
distinct unit groups of one complex), keep the attested name and enforce a
*structural* invariant instead: same name ⇒ pairwise distinct `status` +
pairwise disjoint `units_included` (see `tests/test_reference_integrity.py`).
Aggregators and fixes must never synthesize names ([[project-reference-fix1]],
ticket 0416).
