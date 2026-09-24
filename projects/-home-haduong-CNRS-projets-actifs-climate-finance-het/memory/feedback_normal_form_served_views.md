---
name: feedback_normal_form_served_views
description: "The author wants served observatory views in normal form — one file = one table, joins computed at read time — rather than materialized indexes, raised size guards, or SQLite (decided 2026-09-22, ticket 0858)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a12625da-f40d-43cd-8b7d-fd6f422a6920
  modified: 2026-09-22T08:31:16.947Z
---

Asked 2026-09-22 whether to shrink `documents.json` (975 kB, 85 % of it a
materialized document → facts index), raise the pre-commit size guard, or
move to SQLite, the author chose normal form: `documents.json` is the table
of collection attempts and nothing derived; the fold-outs join the served
tables (`m1a/<CODE>.json`, `observations/<CODE>.json`, `<CODE>.json`,
`reviewed-evidence.json`) in the client, loaded once per country on demand.
Ticket 0858 delivered it (PR #1443): 152 kB, zero measured difference
against the old index, one build-order constraint removed.

**Why:** a join computed at read time cannot drift from its tables; a
materialized copy can, and it grows with every collection. Raising the guard
freezes the cost; SQLite is a database for a spreadsheet-sized corpus and
adds a binary artifact the guard exists to block. SQLite is deferred to M2,
when live refresh makes the corpus grow and queries ad hoc.

**Superseded in part (2026-09-23, ontology v2 merged as #1449):** a derived
SQLite file under `data/derived/jetp/` is now the build and validation engine
(`docs/jetp-ledger-storage.md` section 3), never committed; CSV in git stays
the record and the browser still joins one JSON file per table. Normal form
stands.

**How to apply:** when a served JSON view starts carrying data another view
already holds, split by table and join in the client instead of adding keys
or raising limits. The country views `<CODE>.json` still mix projects,
sources and coverage: a second step, to decide with the public format (0727).
Related: [[feedback_escalate_procedural_vs_substantive]].
