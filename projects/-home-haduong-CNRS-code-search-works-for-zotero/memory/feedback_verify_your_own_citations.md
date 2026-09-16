---
name: feedback-verify-your-own-citations
description: "Review your own work by re-deriving its citations and figures from source, never by re-reading its prose."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: af8462f8-814a-41dd-8e1e-b4beb1839a7a
  modified: 2026-09-15T21:13:49.454Z
---

Re-reading a document you wrote checks whether it says what you meant. It cannot
check whether what you meant is true, because you will read the sentence and
recall the intent instead of testing it.

**Why:** on 2026-09-15 I published, twice, that `refreshQueue()` in
`plugins/sdt-sitter/scheduler.js` was "called only at 176" and therefore
unreachable while the drain loop spins — so `state.pending` was "a photograph,
not a live count". Two merged artifacts and a ticket carried it. Asked for a
proportionate review, I wrote a script that re-derived all 27 figures of the
incident file from the raw shutdown JSON and checked each code citation against
the line it named. The figures were all right. The script also printed that
`refreshQueue()` appears at 113 and 382 as well — `record()` calls it, and the
drain calls `record()` every iteration. The claim was false, and with it fell a
conclusion I had relayed to the author and to a peer session: "the sitter
recovers unaided once the source stops", which rested entirely on reading a
`pending` climb as proof the drain had emptied.

Nothing in the prose looked wrong. The grep that found it was aimed at
confirming a line number, not at doubting the sentence.

**How to apply:** when reviewing your own output, review the *inputs* — re-run
the measurement, re-resolve every file:line, re-derive every number from the
artifact it came from, and let the script print neighbours you did not ask about.
Budget the review by the risk of the claims, not the size of the diff: a
documentation PR's whole risk is that a figure or a citation is wrong, so a
script that re-derives them is the proportionate gate, and re-reading it is not a
gate at all. Separate what was measured from what was inferred before publishing,
and state which is which — the measured part of that incident survived intact;
every casualty was an inference wearing a citation. Related:
[[feedback-verify-the-load-bearing-claim]], [[feedback-probe-needs-discriminating-control]],
[[feedback-no-past-tense-without-a-run]].
