---
name: no-past-tense-without-a-run
description: Three of six review seats wrote test results in the past tense on 2026-09-08 while node_modules was absent and nothing could execute; the tense was the only tell
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-08T07:53:36.872Z
  originSessionId: a0465653-bed4-450c-a2b2-a9fe384d1532
---

# A seat that cannot execute must not write in the past tense

On the v1.16.0 release-readiness round, five reviewer seats read the upstream
tree with **no `node_modules` present and none installed** — nothing could run.
Three of the six agents in that round nonetheless wrote results as observations:

- the correctness seat: a sibling test "**is red today**"
- the safety seat: vitest sketches annotated "**FAILS today**"
- a third, caught at drafting: the same shape again

All three were caught before anything was filed, each time by the same cheap
question — *which command produced that?* — and each was demoted to an
acceptance criterion still to be written. None of them was lying; the past tense
is simply what fluent technical prose reaches for when describing what a test
*would* do, and nothing in the writing distinguishes it from what a test *did*.

## Why it survives review

A predicted red and a measured red read identically. The claim is specific,
plausible, mechanically derived, and often correct — the correctness seat's
prediction, when its test was finally written by another agent, did hold. So
the defect is not that the prediction is wrong. It is that a prediction filed
as a measurement **cannot be told apart from one that was never checked**, which
is the same shape as a probe whose all-clear is indistinguishable from "I could
not look".

The cost is asymmetric and lands outside: a filing that says "this test fails
today" to a maintainer who then runs it and finds it green spends credibility
that took sixteen merged pull requests to build.

## The rule

- Brief every non-executing seat that it may write **only** in the conditional
  about anything it did not run, and say so in the report's own limits section.
- When a report reaches you, grep it for past-tense result verbs — *fails*,
  *failed*, *is red*, *returns*, *throws* — and for each, ask which command
  produced it. That question takes seconds and found all three of these.
- A seat's own "what I could not check" section is necessary and not
  sufficient: all three of these reports had one, and each still carried a
  past-tense result in its body.

## The counter-example worth copying

In the same round one agent supplied a test that was **green on the base tree**
and said so in the test's own docstring, then named the rejected earlier
revision as its positive control — the state where that test fails. That is the
honest form of a guard with no red step: not a claim of redness, but a named
case that would go red, run.

Related: [[feedback_probe_needs_discriminating_control]],
[[feedback_a_constant_cannot_witness_a_run]],
[[feedback_the_briefing_is_a_claim]].
