---
name: hold-out-the-answer-key
description: "Ground truth the system itself consumes is circular; score against an independent source with the consuming tier disabled, and ask whether \"mechanical\" scoring secretly needs the same alignment the system performs."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b08b8b4d-9301-45d4-9a9d-09e3ea52cd9b
  modified: 2026-09-02T08:53:22.891Z
---

X5 as propagated on 2026-09-01 scored seg/1's cuts against each document's
printed table of contents — the same list §5.2.2 makes seg/1 collect candidates
from and validate against. A passing score would have certified "parsed the
contents list", not "found the boundaries", and documents without a list had
no ground truth at all. Worse, the "mechanical" scoring the 2026-08-31 ruling
promised needed the body location of each contents entry, which is the very
alignment seg/1 performs; the only independent comparison, by page, needs
exact page breaks, present on ~55 % of caches.

The ruling (2026-09-02): ground truth is the PDF's embedded outline, with the
segmenter's outline tier disabled on those documents, so the layout tier and
seg/1 are what get scored; human scoring where no outline exists; 50 cuts per
class, verdicts never pooled. Same-day sibling: the fallback-size deferral,
[[deferral-must-name-a-measurer]].

**Why:** the red-team seat found it; two earlier review passes and the author's
own reading had not, because the circularity hides in the word "own" ("its own
table of contents") and in "mechanical", which sounds like a property of the
source rather than a claim about a scorer nobody had designed.

**How to apply:** for any experiment rule, name the ground-truth source and
grep the design for where the system reads that same source. If it does, hold
that tier out of the measured configuration or pick a source the system never
reads. Then ask what the scorer must compute to compare — if it is the
system's own hard step, the scoring is not mechanical, and the brief says so.
Related: [[probe-needs-discriminating-control]], [[metric-decides-the-verdict]].
