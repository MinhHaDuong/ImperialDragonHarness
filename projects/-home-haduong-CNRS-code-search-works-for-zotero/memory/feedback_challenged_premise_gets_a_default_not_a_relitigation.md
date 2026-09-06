---
name: challenged-premise-gets-a-default-not-a-relitigation
description: "when the author doubts a feature's premise late, offer a flag with a measured default — not a re-argument and not silent compliance"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c570dc22-4288-449b-bdf4-d73b04a3e471
  modified: 2026-09-01T11:31:58.660Z
---

At the 0091 PR 2 finish line (2026-09-01), the author said the premise —
unaccented queries must reach accented documents — convinced him little, and
asked if the expansion could be optional. The measurement had already crowned
expansion; re-arguing the premise or ripping the feature out were both wrong.

**Why:** the premise was contested per-user, not falsified: expansion
compensates a recall regression the un-folding creates, so off-by-default
would regress stock behavior, while always-on overrides the author's doubt.
A flag defaulting to the measured-safe side prices the premise per user
instead of ruling it once for all. Cost: one env var, four tests, one
appended commit (kept the stacked PR 3 valid). The author approved in one
word.

**How to apply:** when a ruling-holder challenges the *why* of an already
measured winner, respond with the option brief (rules memory
[[decision-briefs]]): name the regression each default direction causes, and
recommend flag-plus-default on the side the measurement protects. Append the
commit rather than amend when siblings stack on the tip.
