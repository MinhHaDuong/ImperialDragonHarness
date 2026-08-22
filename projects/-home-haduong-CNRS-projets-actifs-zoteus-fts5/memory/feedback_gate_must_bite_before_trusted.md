---
name: feedback_gate_must_bite_before_trusted
description: A verification gate is worthless until sabotage proves it fails; two gates in one session passed while the property they guarded was broken
metadata:
  type: feedback
---

A gate that has never been seen to fail is not a gate. Twice in the zoteus-fts5
chantier (2026-08-21) a gate was green while the property it guarded was broken:

- The FTS5 ranking gate asserted "every query's top-3 is a subset of the JS
  index's top-5". It stayed green with the store's `ORDER BY` **reversed**,
  because each fixture query matched only two or three items, so the subset
  relation held whatever the order was. Fixed by a graded-relevance corpus:
  eight same-length passages repeating the query term eight times down to once,
  so all match and only ranking separates them.
- A first sabotage attempt on the vector direction guard reversed the SQL
  `ORDER BY` and reddened 19 tests — but `vec0` rejects that at `prepare()`
  time, so it broke the *mechanism*, not the ordering, and proved nothing. The
  honest sabotage was `.reverse()` on the returned array: 3 tests red, every
  fused test still green, because `rrf()` ranks by list position and a reversed
  list is still a list.

**A gate fails in two directions, and the second one was new to me
(2026-08-22).** A checker written to catch stale figures compared against a
thousands separator the documents did not use — a narrow no-break space had
leaked out of the French prose into the checker's own source — and it reported
**all fifty pairs stale**. That is not a gate that never fires; it is one that
fires on everything, and it is retired by its reader just as fast. Sabotage
answers "does it bite?"; the clean tree answers "does it stay quiet when it
should?", and both readings are needed before the gate is worth anything.

The same session produced a third variant worth naming: a test whose sabotage
did *nothing*. Reverting the exact-slot comparison to the substring test it
replaced left the suite green, because a sibling guard already made the two
equivalent. The test was renamed for what it observes rather than the mechanism
it was assumed to cover, and the load-bearing guard was identified by
sabotaging each candidate in turn. A test that cannot be made to fail by
breaking the thing it names is testing something else.

**Why:** this is the general form of the rule already in `coding-bash.md` — a
check whose all-clear is indistinguishable from "I could not look" is not a
check. It bites hardest on *refactors*, where the suite was written against the
old implementation and passes on a new one that quietly changed behaviour.

**How to apply:** before trusting any new gate, break the thing it guards and
watch it fail. Then check *which* test failed and how many — a sabotage that
reddens the whole file usually broke the mechanism, not the property. Prefer a
fixture where the property is the *only* thing that can separate outcomes. See
[[feedback_cited_evidence_ages_out]].
