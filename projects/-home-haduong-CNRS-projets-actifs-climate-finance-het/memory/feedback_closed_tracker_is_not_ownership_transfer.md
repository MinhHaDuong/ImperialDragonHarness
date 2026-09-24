---
name: feedback_closed_tracker_is_not_ownership_transfer
description: "A closed migration tracker can hide a migration that never happened — check who writes the tables, not whether the tickets closed; scan open PRs before designing"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 54fc6cbe-6aff-4687-a568-0cb4be7ed8a5
  modified: 2026-09-23T08:11:01.144Z
---

JETP backend tracker 0760 (children 0761–0770) closed overnight 14→15 Sept 2026
as "migrated", yet every country doc said write ownership stayed legacy and none
of the canonical stores existed. Its criterion "no duplicate authority" held
vacuously because nothing moved. I first reported "schemas not implemented" from
the design note, then "migration done" from ticket state — both wrong.

**Why:** closure records that criteria were ticked, not what changed. An
all-clear that cannot distinguish "migrated cleanly" from "never migrated" is
not a check.

**How to apply:** before stating a migration's status, look for the target
tables on disk and read which code path the build actually reads
(`build_observatory.py` TABLES). Also scan open PRs' files *before* designing a
plan: on 2026-09-23 a sibling PR (#1449, ontology v2 + 0870 train) already held
the author's decision that contradicted my table-by-table cutover; I only found
it at the pre-push scan. See [[feedback_parallel_work]], [[feedback_gate_verify_branch_not_pr_body]].

Outcome of that session: ledger language pinned to ODEM (`docs/jetp-language.md`),
ontology split into ontology / ledger-storage / ledger-migration docs, MVP page
vocabulary is a newsroom's (`docs/jetp-observatory-presentation.md`), merged as #1449.
