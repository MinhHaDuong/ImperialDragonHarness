---
name: feedback_design_for_target_schema_not_legacy
description: "Observatory UX proposals must follow docs/jetp-language.md's D1–D4 pipeline and the migrated tables, never the legacy tables the site still serves; labels carry ontology words, no step codes"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 236bb3a1-5c92-4943-8e87-7057c9e6f7c5
  modified: 2026-09-24T19:39:02.866Z
---

When proposing observatory navigation or page structure, design for the migrated ledger tables (`lines`, `observations`, `referents`) and name pages with the ontology's words from `docs/jetp-language.md`. Don't design around the legacy tables the site still serves (`events.csv`, `project-source-links.csv`). Never put step codes (D1, D2…) in labels.

**Why:** On 2026-09-24 I reasoned from the served legacy data and concluded "Rows and Statements are siblings". The language doc defines a linear D1→D4 pipeline, and the author corrected me: "use the language from the ontology, design for the migrated tables NOT legacy". When I offered labels like "Lines · D2", the reply was "No codes in labels, stupid".

**How to apply:** Before any IA proposal, read `docs/jetp-language.md` first, then `docs/jetp-ledger-migration.md`. The author's principle: the navigation menu follows the data pipeline and the ontology. The paper trail is a viewer on the CSVs; the tallies hold everything derived, one page per country and one per theme (ticket 0956). Related: [[feedback_verify_before_advising]].
