---
name: feedback_memory_batch_lands_as_three_things
description: "A memory entry is an index line, a body file and a provenance record; committing any subset leaves a dangling pointer, an unreachable body, or a red gate"
metadata:
  type: feedback
---

On 2026-09-16 a batch of twelve memories written by several sessions sat
uncommitted in the shared checkout. It looked like two separable problems — an
index carrying foreign lines, and untracked body files — and the owner proposed
landing only its own two. Measuring the correspondence settled it: twelve index
lines, twelve bodies, zero pointers without a body and zero bodies without a
pointer. The unit was twelve, not two, because a `MEMORY.md` cannot be staged in
thirds.

There is a third component, and it is the one that is invisible until CI fires.
`tests/test_provenance_coverage.py` asserts every live memory body has a record
in `memory/.provenance.json`. Landing bodies and index lines without records
turns the gate red; the batch above was, at that moment, making the test fail in
the primary checkout while passing in CI, because the bodies were on disk and
not in the tree.

**Why:** the three artifacts are one fact stored in three places, and each
partial commit fails differently. Index line without body: a dangling pointer
that reads as a memory until someone follows it. Body without index line: an
unreachable memory, since the resident index is the only door
([[reference_no_recall_channel_fires]]). Either without a provenance record: a
failing gate, and a promotion frequency count that no longer reflects reality.

**How to apply:** when landing memory, stage all three or none, and verify the
correspondence in both directions before committing rather than trusting that
you wrote them together. When a batch spans several authors, the unit is the
whole batch — do not carve one author's share out of a shared index file. Note
that `skills/dream/provenance.py record` cannot be pointed at a worktree
(ticket 0934), so from a worktree the record must be written into the JSON by
hand or the whole batch landed from the primary checkout. Related:
[[feedback_ask_the_live_peer_before_committing_its_work]].
