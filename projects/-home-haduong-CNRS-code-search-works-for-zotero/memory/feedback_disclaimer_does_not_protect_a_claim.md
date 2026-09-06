---
name: feedback_disclaimer_does_not_protect_a_claim
description: "A field saying \"which budget row applies is a ruling, not a measurement\" did not stop the same document asserting a row two paragraphs later"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e638f30e-5d01-4ff0-be22-bf1aac1cf0db
  modified: 2026-09-03T11:28:16.543Z
---

The 0120 artifact carried `what_this_does_not_settle`: "which C3 row a keyword build's
server process answers to is a ruling, not a measurement." The prose of the same
document then read 730,6 MiB as "level with C3's ~750 MB" and called it pressure on a
ceiling. Both the author and a peer session read past the disclaimer; the author
challenged the comparison and it collapsed (2026-09-03).

Two separate failures, and the second is the reusable one:

1. **A disclaimer in one field does not protect a claim made in another.** Writing the
   caveat discharged the feeling of having been careful, and the claim went in anyway.
2. **Check that a budget's topology applies before comparing a measurement to it.**
   C3's two ~750 MB rows describe SPEC.md §5.2.5's multi-process design — servers
   holding no model beside one embedding service that does. The measured binary was
   stock upstream v1.12.0, single-process. I had *established that myself*, with a grep
   for `new Worker`/`child_process`, one commit earlier, and still made the comparison.
   A budget written for a topology the binary does not implement can be neither
   exceeded nor respected; the comparison is void, not tight.

**Why:** a specification's numbers carry an unstated scope — which process, which
topology, which regime. A measurement and a budget that name the same unit are not
therefore comparable, and the number's familiarity is what makes the mismatch invisible.

**How to apply:** before writing "X is at/over/under the budget", state which entity the
budget binds and check the measured entity is that one. When the answer is "no row
applies", say that instead of picking the closest row. And treat a disclaimer as a
prompt to re-read the body for the claim it disclaims — if the body does not need
changing, the disclaimer was decoration.

The salvage was worth more than the claim: the trajectory (flat through the metadata
pass and the whole attachment walk, climbing only with full text, flat again after) is
evidence *for* C3's property that RAM is independent of library size. Relaying it as
pressure on the number was close to backwards.

Related: [[feedback_verify_the_load_bearing_claim]],
[[feedback_adopted_constants_carry_mechanisms]],
[[feedback_room_for_multilingual_embedders]].
