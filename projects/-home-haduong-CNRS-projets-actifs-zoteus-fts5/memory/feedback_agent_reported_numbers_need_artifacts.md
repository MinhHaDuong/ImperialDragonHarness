---
name: feedback_agent_reported_numbers_need_artifacts
description: A measurement an agent reports in prose but never writes to a file is not evidence; require the driver to record its own environment and results
metadata:
  type: feedback
---

A subagent that runs a benchmark and reports the figures in its final message
has produced **prose, not evidence**. If the driver only `console.log`s to a
stdout nobody captured, the numbers cannot be re-derived, and nothing in the
repo distinguishes a real run from a plausible one.

This bit hard on zoteus-fts5 PR #2 (2026-08-21). Migration peak RSS, isolated
wall-clock, and database sizes were published in `STATE.md` and a tracker
ticket as "measured", with the PR body claiming "raw artifacts committed". A
reviewer grepped: none of those numbers appeared in any committed file, and the
artifacts that *did* exist showed RSS **falling** as file size rose —
contradicting the flat-memory story built on them. Re-measuring with capture
changed the conclusion: file x3,05 gave memory x1,20, sublinear rather than
flat, and the isolated migration was 42,7 s rather than the reported 28,4 s.

**Why:** the failure is invisible from the inside. The agent was not lying; it
measured, then let the measurement evaporate. Everything downstream — ticket,
STATE, PR body, and the report that would have gone upstream — inherited a
number with no provenance.

**Producing missing evidence is not bookkeeping — budget it as real work.**
zoteus-fts5, 2026-08-22: a review blocked three claims for having no committed
artifact. Generating those artifacts was expected to be clerical. **Two of the
three claims turned out to be wrong.** 0009's codepoint sweep, described in
prose as "22 divergences, all toward retrieving less", actually had twelve
divergences in the *wrong* direction — the ticket's own defect class, unfixed.
0013's "the effect almost entirely cancels" became "order moves in about half of
queries" once measured through the real ranker over 72 queries instead of a
re-implementation over four. Only the third reproduced. So a demand for
provenance is not pedantry about filing: it is the cheapest available test of
whether the claim is true.

**How to apply:** when a task is a measurement, make the *driver* write a file
containing the results **and the environment that produced them** — env vars
that matter (`NODE_OPTIONS`), interpreter version, input sizes, and the metric
read (prefer `VmHWM` from `/proc/<pid>/status`: a kernel high-water mark cannot
miss a peak between samples, where a `ps` sampler can). Commit that file. Then
verify the prose against it before publishing, and grep the artifacts for every
headline figure. Related: [[feedback_gate_must_bite_before_trusted]],
[[feedback_cited_evidence_ages_out]].
