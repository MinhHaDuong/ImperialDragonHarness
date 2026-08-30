---
name: feedback-benchmark-harness-traps
description: "An A/B microbenchmark measures the harness as much as the code — polymorphic call sites, single runs, a missing control arm, and a missing null alternative each produced a wrong or unusable answer"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6f316c3e-3800-40bd-bb02-33c301abd583
  modified: 2026-08-30T09:24:20.787Z
---

Traps that produced wrong or unusable answers on this project. All are
properties of the measuring apparatus or of the measurement's design, not of
the code measured.

**One call site, two callees, no inlining.** A harness shaped
`function scan(f) { for (row of rows) acc += f(q, row) }`, called once with the
old implementation and once with the new, makes that call site polymorphic —
V8 then declines to inline *either*. Measured 1,61x; giving each variant its
own scan with a direct call measured 2,48x. Give every variant its own
monomorphic call path.

This is the same defect the change itself fixed, which is why it is worth
remembering: a shared helper taking `number[]` from one caller and
`Float32Array` from another costs ~1,9x at the call site. The trap and the bug
are one phenomenon, and a harness built carelessly reproduces the bug it is
measuring.

**Single runs disagree by ±15%.** One run each invented a 2,9x that five
interleaved repetitions did not support (2,19x). Interleave A/B/A/B so drift
hits both arms, take medians, and report the spread — the heavier arm is the
noisier one, so a naive comparison flatters whichever side does more work.

**A measured number with no control arm cannot be attributed** (2026-08-29,
X2). Deleting a query stoplist measured a p95 of 1 773 ms against a ~500 ms
budget — a clean fail, and worthless on its own: nothing in it said whether the
deletion caused the cost or whether a 20-term OR query over 477k passages
simply costs that much. Building stock upstream and running the identical
queries on the identical index answered it (392 ms, so 4,5x attributable) and
took twenty minutes. This is the non-null twin of the harness rule that a null
needs a positive control: **a large result needs a baseline arm before it names
a cause.** Budget the second arm into any measurement that will drive a
ship/don't-ship decision — it is usually a rebuild and a rerun, not a new
experiment.

**Measure the null alternative before optimising the component** (same
session). The project maintains a keyword layer over a Zotero library;
nobody had ever timed Zotero's own built-in search. It turned out slower than
both arms (p95 4 199 ms), unranked (median query matches 307 items in
modification-date order) and item-level rather than passage-level. That single
measurement reframed the work: the layer earns its place through *ranking and
passage results*, not through matching — so the whole stoplist question sat in
the half that was not where the value was, and the right call became "do not
spend an upstream slot on this". Ask early what the user would do without the
component; a cheap baseline can retire a whole line of work.

**An artifact that omits its SHA mislabels every later comparison** (2026-08-30,
X3a wall time). `0011-rss/uncapped-build-3.json` recorded no commit; when a new
run halved its 371,6 s, the ticket compared against it as "stock upstream" —
provenance archaeology then showed the old run was this project's own abandoned
FTS5 prototype, a *sibling* implementation, so the comparison was
apples-to-cousins and the "trunk got faster" framing was wrong. Every result
JSON carries the SHA of the code that produced it, written at run time; a
comparison against an artifact with no SHA is a claim about an unknown.

**How to apply:** measure the *shipped* artifact (import the built `dist/`),
not a hand-copy of the patch — a hand-copy silently omits later edits. Assert
equivalence over the whole real store rather than a fixture. Treat a speedup
from one run of each arm as not yet a number. And before reporting any figure
as a verdict, ask what it is being compared against — the previous
implementation, and the alternative the user already has.
Related: [[feedback-execute-authorized-outward-actions]],
[[feedback-verify-the-load-bearing-claim]].
