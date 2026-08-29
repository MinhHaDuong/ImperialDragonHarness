---
name: feedback-benchmark-harness-traps
description: "An A/B microbenchmark measures the harness as much as the code — one call site with two callees, and single runs, both produced wrong speedups"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6f316c3e-3800-40bd-bb02-33c301abd583
  modified: 2026-08-29T08:44:06.628Z
---

Two traps produced three different wrong answers for the same change on
2026-08-29 (upstream cosine fusion, ticket 0070). Both are properties of the
measuring apparatus, not of the code measured.

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

**How to apply:** measure the *shipped* artifact (import the built `dist/`),
not a hand-copy of the patch — a hand-copy silently omits later edits. Assert
equivalence over the whole real store rather than a fixture. And treat a
speedup from one run of each arm as not yet a number.
Related: [[feedback-execute-authorized-outward-actions]].
