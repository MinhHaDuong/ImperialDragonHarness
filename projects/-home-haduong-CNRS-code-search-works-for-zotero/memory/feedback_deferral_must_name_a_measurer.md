---
name: deferral-must-name-a-measurer
description: "A design \"policy\" that replaces a number, and a deferral of that number to an experiment, are both void unless the bound exists and the experiment can measure the quantity — check both before writing \"left to X\"."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b08b8b4d-9301-45d4-9a9d-09e3ea52cd9b
  modified: 2026-09-02T08:53:10.046Z
---

On PR #157 (ticket 0502, 2026-09-02) the propagation replaced seg/1's ~6k-token
fallback size with "the largest synthetic entries the downstream geometry
accepts" and deferred the number to X5. Both halves were empty: nothing
downstream bounds an entry's size (chunks stop at entry boundaries, the work
order packs its own token budget, entry collapse yields one hit per entry
whatever its length), and X5 samples *accepted* boundaries while the fallback
fires exactly where there are none. The scope review caught it as "a policy
without a number"; the real defect was that the policy named a bound that does
not exist and the deferral named an experiment that cannot look.

**Why:** a deferral reads as discipline ("not invented here") while quietly
turning a design decision into nobody's. The author ruled one constant (~12k)
in one line once the void was shown.

**How to apply:** before writing "the number is left to X" or "the largest
the geometry accepts", answer two questions in the text: which sentence of the
spec bounds it, and which experiment's sample contains the case. If either
answer is none, it is a choice, and the brief goes to the author now — see
[[decision-briefs]] for the form, and [[hold-out-the-answer-key]] for the
sibling defect found in the same review.
