---
name: project_jetp_three_stages_m1a
description: "JETP data has three stages in the author's vocabulary (raw documents, structured extraction, reconciled facts); M1a means the MVP explores all three, not CSV downloads — tracker 0834, acceptance cases ZAF and VNM"
metadata: 
  node_type: memory
  type: project
  originSessionId: b5a60d4e-2e95-41b2-bf5c-51ffa295522e
  modified: 2026-09-17T17:01:45.426Z
---

Decided 2026-09-17. The JETP data pipeline has three **étages** (stages), in
the author's words: (1) documents bruts — the downloaded PDF/HTML archived by
hash in DVC, register `data/jetp/manifest.csv`; (2) extraction structurée —
tables pulled from those documents (M1a inventories, ledger atomic
observations); (3) faits réconciliés — canonical records and country views.
The August 2026 conception note's "trois couches" (CRS/IATI, official tables,
prose) is a *source typology*, not this; and M1a's "six source layers" are
sub-layers of stage 2. Say "sous-couche d'extraction", never "layer", to the
author.

M1a is *not* reached by ticket 0832 (frozen CSVs + download buttons). It is
redefined by tracker 0834: from any fact, drill to its extraction rows, then
to the document and page; from any document, climb back. Children 0835–0839,
one sign-off unit each. Acceptance cases: South Africa (JET register dashboard
snapshot, 258 records × 21 fields, M1a kept only 8 fields → 0837) and Viet Nam
(RMP 2023 annexes, 279 positions with page locators; the July 2025 portfolio
of 3 named + 21 undisclosed is a separate object, no link before M1b).

**How to apply:** when a JETP ticket says "publish" or "download", check it
against 0834's acceptance criterion before executing. See
[[feedback_exit_criteria_carry_author_intent]].
