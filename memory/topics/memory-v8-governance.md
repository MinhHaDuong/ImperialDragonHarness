# Memory v8 governance

Scope: how project memory is governed in this repository under the v8
convention — design boundaries, legacy retirement, and what the retired
legacy advice was. Facts here come from the journal entries and design
documents cited below.

## Supported observations

The v8 design was adopted and delivered through PRs #1093, #1096 and #1097,
then the convention and source inventory (0911/0917) through PR #1102, which
also retired the native/shared-store DREAM helpers (`commit.py`,
`read-index.py`, `provenance.py`) with their consumer tests. The pilot
activating the convention in this repository was decided 2026-10-02: public
audience for themes and journal, a declared private companion for uncleared
material, and initial sources limited to the ten `memory/` root files in the
inventory. Roar captures facts; DREAM consolidates without rule promotion;
the journal is append-only. The pilot declaration is
[docs/memory-v8/pilot.md](../../docs/memory-v8/pilot.md).

## Sources and exceptions

- [2026-10-01: memory v8 design and boundaries](../journal/2026/2026-10-01-memory-v8-design-and-boundaries.md) — design adoption.
- [2026-10-01: legacy provenance helper retirement](../journal/2026/2026-10-01-memory-helper-retirement.md) — helper removal with controls.
- [2026-10-01: portable registration review](../journal/2026/2026-10-01-portable-registration-review.md) — registration PR review.
- [2026-10-02: PR 1102 merge under parallel housekeeping](../journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md) — delivery merge record.
- [2026-10-02: memory v8 pilot established](../journal/2026/2026-10-02-memory-v8-pilot-established.md) — pilot activation.
- [Legacy retirement record](../../docs/memory-v8/legacy-retirement.md) — removed execution paths and recovery.
- [Retired legacy feedback: rules from consolidation](../feedback_rules_come_from_memory_consolidation.md) — historical evidence only; its advice to derive rules was superseded by v8 and the author's 2026-10-01 RETIRE LEGACY direction. Kept as history, never current authority.
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
