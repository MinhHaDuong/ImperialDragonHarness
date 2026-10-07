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
audience for themes and journal, and initial sources limited to the ten
`memory/` root files in the inventory. As first recorded, uncleared material
was to go to a separate private companion; that clause was superseded the
same day by the author's encrypted-in-repo decision — uncleared material
stays in this repository as age-encrypted `.age` ciphertext from birth,
plaintext never in the tree, the key under `~/.config/keys` and never
tracked (PR #1112, mechanics pinned by 0988). Without the key an entry is
existing but unreadable: dream skips it and reports the count, never
treating it as empty. Roar captures facts; DREAM consolidates without rule
promotion; the journal is append-only. The pilot declaration is
[docs/memory-v8/pilot.md](../../docs/memory-v8/pilot.md); this correction
was made by the [first dream](../dreams/2026-10-02-pilot-first-dream.md),
which cites the sources below. The pilot's evaluation protocol was
committed to main before its acceptance trials on 2026-10-02
([evaluation protocol](../../docs/memory-v8/evaluation-protocol.md), PR
#1137); the trial experiences are consolidated under
[acceptance trial](memory-v8-acceptance-trial.md) and their cell verdicts
live in the [results document](../../docs/memory-v8/evaluation-results.md),
not in memory.

After the trial (verdict "No rollout"), the two recorded blockers were
cleared on evidence by PRs #1147 (codex) and #1150 (pi on the local server)
and tracker 0909 closed on 2026-10-02. Ticket 0913, the standing rollout
workpackage, closed through PR #1212 on 2026-10-06; 0912 and 0919 were closed
as superseded v7 scopes (PR #1205). On 2026-10-05 the author adopted Brood
(PR #1187, ticket 0888): project-local proofs of concept, harness nomination
tickets only, and separately assigned harness generalization; it permits
evidence-based edits to consolidated memories while the journal stays
append-only, and leaves Dream and Roar authority unchanged. Its evaluation
records procedural fixture results only, not field benefit
([brood evaluation](../../docs/memory-v8/brood-evaluation.md)). The second
dream ([2026-10-07](../dreams/2026-10-07-second-dream.md)) added the
operational topics indexed beside this one.

## Sources and exceptions

- [2026-10-01: memory v8 design and boundaries](../journal/2026/2026-10-01-memory-v8-design-and-boundaries.md) — design adoption.
- [2026-10-01: legacy provenance helper retirement](../journal/2026/2026-10-01-memory-helper-retirement.md) — helper removal with controls.
- [2026-10-01: portable registration review](../journal/2026/2026-10-01-portable-registration-review.md) — registration PR review.
- [2026-10-02: PR 1102 merge under parallel housekeeping](../journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md) — delivery merge record.
- [2026-10-02: memory v8 pilot established](../journal/2026/2026-10-02-memory-v8-pilot-established.md) — pilot activation.
- [Orchestrated raid closes 0909](../journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md) — trial blockers cleared.
- [Brood adoption](../journal/2026/2026-10-05-brood-adoption-pr1187.md) — author decision, PR #1187.
- [Raid 926/912/919](../journal/2026/2026-10-05-raid-926-supersession-and-publication.md) — 0912/0919 superseded.
- [0913 close path](../journal/2026/2026-10-06-0913-dispatch-close-path.md) — rollout workpackage closed.
- [Legacy retirement record](../../docs/memory-v8/legacy-retirement.md) — removed execution paths and recovery.
- [Retired legacy feedback: rules from consolidation](../feedback_rules_come_from_memory_consolidation.md) — historical evidence only; its advice to derive rules was superseded by v8 and the author's 2026-10-01 RETIRE LEGACY direction. Kept as history, never current authority.
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
