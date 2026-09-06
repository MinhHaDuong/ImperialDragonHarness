---
name: feedback-two-gate-channels-find-different-defects
description: "A gate's own verification and an independent review are not redundant: on one PR each found a defect the other missed, and the review's was the blocking one"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-02T22:00:00.000Z
---

Gating PR #226 (ticket 0579, goal-2 acceptance gates), 2026-09-02. I ran my own
verification channel hard: reproduced `make acceptance-fixtures`, mapped every
fail-control to the clause it reddens, read the assertion source, and built a
**positive control** by deleting one fail-control from `NAMES` — the gate went to
exit 1 naming the never-red assertion, so the backwards gate is real. I read the
real-target artifact and confirmed R23 was a genuine `fail`, both arms present,
`file_deleted_by_hand: false`, `files_gone: []`.

I had the falsifying data on screen and did not draw the inference. Both arms
recorded `"was": "1"`. Arm 1 restamps the seeded index to `"0"`; the build then
sidelines it out of the `*.sqlite` glob that `_index()` resolves, so arm 2 got a
**fresh empty index**. Its `serving: false` is vacuous — an empty index serves
nothing whatever its stamp. The independent reviewer caught it from the same
artifact I had already read.

**The lesson is not "review harder".** It is that the two channels have different
failure modes and neither substitutes for the other:

- My channel is strong on *did the thing actually run* — controls, reds, exit
  codes, byte-identical regeneration. It is weak on *does the recorded evidence
  support the sentence written about it*, because I read the artifact looking for
  the claim rather than against it.
- The review channel is strong on the second and cannot cheaply do the first
  (it will not usually build a control arm).

So run both, and keep their provenance separate in the bounce: quote the
reviewer's finding as received under its own heading, sign your own observations
as yours. On this PR the write-up had three sections stating "fails in both
directions" — PR body, ticket, README row — and one of the two directions never
happened.

**Generalisation, and it is the repo's own rule turned on the harness:** a
perturbation arm that does not verify its own precondition still produces a
verdict, and that verdict reads exactly like a real one. Where an arm depends on
state a previous arm consumed, take a per-arm baseline and report `not-run` when
it is empty. Same shape as `_no_counters` already does for R3.
