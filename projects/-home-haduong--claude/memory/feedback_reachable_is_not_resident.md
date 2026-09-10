---
name: feedback_reachable_is_not_resident
description: "an entry you can still find is not an entry you know to look for — 'it stays reachable' answers a different question than 'it still works', and for anything that prevents an action the two come apart completely"
metadata:
  type: feedback
---

Designing the memory index as a scored top-N view, I argued that cutting an
entry below the rank was harmless because the body stays on disk and a grep
finds it in 49 ms. A design review killed it in one sentence: **the index buys
*unprompted awareness*, and the cut protects *reachability*.** Those are
different properties.

For an entry whose function is to stop an action before it is taken, falling
below the cut is deletion. The agent never forms the hypothesis that would send
it to the search — not forming it *is* the failure the entry existed to
prevent. You do not search for what you do not know to look for.

The part that stings: the test I had written to guard this would have passed
while the defect ran. "No entry becomes unreachable" is true at the exact
moment a guard entry stops working.

**Why:** the claim was already merged and top-billed as the substantive
contribution. Four reviews had passed over the document; the one that caught it
was the one told to attack the *design* rather than verify the figures.

**How to apply:** when a change makes something "still available", name which
property you are protecting and which you are dropping. Availability, reach,
and being surfaced-without-asking are three different things, and a channel
that supplies the third is not replaced by one that supplies the first. Where
some entries need the third, let them declare it, and gate on *that*: "no
declared entry falls below the cut" is testable, "nothing becomes unreachable"
is a null trap. Same shape as [[feedback_a_test_green_for_an_accidental_reason]].
