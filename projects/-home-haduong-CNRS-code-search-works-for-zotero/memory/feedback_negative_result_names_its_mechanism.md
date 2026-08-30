---
name: feedback-negative-result-names-its-mechanism
description: "A measured \"no\" condemns the mechanism it tested, not the capability the author wants; say which, or he rejects the answer and is right to"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6d672369-cc54-4c48-b252-59897f375392
  modified: 2026-08-29T17:45:15.820Z
---

X4 measured one way of scoping a search — an arbitrary rowid set shipped
through `json_each` — and found it dominated by not scoping at all. I reported
that as the ladder losing a rung and R5 being stuck at `partial`. The author
answered "i don't like what i see, i want to be able to search scoped by
years", and the pushback was correct: a year is a **stored attribute**, so it is
a column with an index and an ordinary predicate, which X4 never touched.
Measured the same day on the same real index, one year costs 254,8 ms by
predicate against 11 141,9 ms by blob — 43x — and against a 207 ms unscoped
baseline the filter is *free*, wider scopes coming out cheaper because the
predicate removes work.

**Why:** a negative result is stated in the vocabulary of the experiment
(`json_each`, rowid sets, a p95) and read in the vocabulary of the capability
("scoping"). The gap between those two is invisible to the person who ran the
experiment and obvious to the person who wanted the feature. Reporting the
verdict without its mechanism boundary is how a measurement that closed one door
gets read as closing the corridor.

**How to apply:** when reporting a measured "no", write the sentence that says
what it does *not* cover, in the same breath as the verdict — "this condemns
rowid-set scoping, which collections and tags need; it says nothing about stored
attributes". Then check whether the thing the author actually asked for falls
inside or outside that boundary, *before* he has to. And when a verdict is
rejected, treat the rejection as evidence about the report's scope rather than
about his patience: here the second mechanism was cheap to measure and inverted
the practical answer within the hour.

The related trap, same session: the real blocker for year scoping turned out not
to be latency at all — the index stores no date, so it was *impossible* rather
than slow. A latency verdict had been standing in front of a capability that no
latency would ever have unlocked. Check that the thing you measured is the thing
that blocks. See [[feedback-probe-needs-discriminating-control]] and
[[feedback-metric-decides-the-verdict]].
