---
name: feedback_guard_one_instance_not_the_class
description: A guard written against the instance you happened to notice does not cover its defect class; enumerate the other places the same confusion can occur
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 67eecdb2-7185-4e46-9b59-8b00cc04acd7
  modified: 2026-08-21T23:52:39.774Z
---

When a defect is understood well enough to be guarded, the guard usually lands
exactly where the author was looking — and the same confusion is almost always
possible somewhere else in the same file.

zoteus-fts5, tickets 0006 and 0012 (2026-08-22). 0006 recognised that Zotero's
local and cloud version sequences are unrelated integers, and guarded it
carefully: the watermark carries an `indexBackend` label, and the delta refuses
to compare across a mismatch, with a comment saying the two sequences are
incommensurable. Nine lines later, the same function handed that library-sequence
watermark to `fullTextSince`, which reads a **different** counter — full-text
extraction versions. Measured on the real library: library version 410 against
full-text versions running to 25 036, so every delta reported **92,7% of the
library** as newly extracted, forever, and could not converge because the number
it advanced belonged to the other sequence. The author had the concept exactly
right and applied it to one axis.

It failed quietly, which is the usual accompaniment: a `maxItems` ceiling capped
the damage, so the symptom was wasted requests and lost updates rather than an
error.

**Why:** understanding a defect and enumerating its instances are different
tasks, and finishing the first feels like finishing both. The comment explaining
why the guard is needed is what makes this easy to miss on review — the reviewer
reads a correct explanation and stops.

**How to apply:** having written a guard, ask what *kind* of thing it protects
against and grep for the other places that kind occurs — the same value handed
to a different consumer, the same comparison on a different axis, the same
assumption in a sibling function. Where the class is "two quantities that must
not be compared", the durable fix is usually to make them different types or to
name them differently, so the next confusion is a compile error rather than a
guard someone has to remember to write. Related:
[[feedback_gate_must_bite_before_trusted]],
[[feedback_agent_reported_numbers_need_artifacts]].
