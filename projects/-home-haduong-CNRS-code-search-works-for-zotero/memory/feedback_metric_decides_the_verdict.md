---
name: feedback-metric-decides-the-verdict
description: Self-referential recall prices an approximation ten times harsher than a task with an outside target — pick the metric before believing the verdict
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7ce0f50f-b53b-407a-bd9c-be06ca722c5f
  modified: 2026-08-29T11:22:11.384Z
---

Before concluding that an approximation is too lossy, ask what it was scored
against. A metric that compares an approximation to **the exact output of the
same model** counts every reshuffle among near-equivalent neighbours as a loss.
A user does not experience a reshuffle among equivalents as a loss. The two
readings differ by roughly a factor of ten, and they support opposite decisions.

**Measured, 2026-08-29, ticket 0025 X1 recall half.** Truncating a Matryoshka
embedding from 1 024 to 256 dimensions:

- rank agreement against the model's own exact top-30: **1,0000 → 0,7783**, a
  22-point collapse
- a retrieval task with a target outside the model (same-item, non-adjacent
  passages): **0,4935 → 0,4699**, a 4,8% cost

Both figures are correct. Only the second describes what a user would notice.

**Why this is easy to get wrong twice.** Rank agreement is the RIGHT metric for
a quantizer — it isolates what the shortcut costs — so reaching for it is not a
blunder. The error is treating it as a quality metric. Acting on the first
number, I wrote to the author that Matryoshka was "probably the wrong lever";
the task metric arrived an hour later and reversed it. Ticket 0008 had already
recorded the same gap from the other side — recall 0,628 while 0,994 of the
top-30's cosine mass was retained — and filed it under "a consolation worth
recording". It was not a consolation. It was the measurement that decides the
design, misfiled as a footnote for a year.

**How to apply.** A self-referential metric cannot compare two models either:
each is its own reference, so a good model and a bad one both score 1,0 against
themselves. Comparing models needs a target outside both. A corpus usually
supplies one for free — in a reference library, passages of one document are
about the same thing. Exclude adjacent chunks when the chunker overlaps, or the
task measures near-duplicate detection, saturates, and would rank a bag of
characters above a language model.

State which question each number answers, in the artifact, next to the number.
Related: [[feedback-verify-the-load-bearing-claim]],
[[feedback-benchmark-harness-traps]].
