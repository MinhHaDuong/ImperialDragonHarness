---
name: feedback-guard-the-silent-failure-first
description: "When writing a parser or validator, the loud guard is the one you think of; enumerate the silent failures deliberately and mirror the upstream validator instead of inventing a contract"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51ae61d2-1e06-4fcf-97e1-66b572d68709
  modified: 2026-08-29T11:55:36.554Z
---

Writing the SDT pack reader (2026-08-29, PR 33), I built exactly one guard —
refuse an unknown pack version — and wrote a test proving it fires. The module
docstring even argued the right principle: "the failure that would cost us is
not a crash on a new layout but a silent misparse". Then `/gaze` found that
`block_starts` went unvalidated, so flattening that series made every chunk
report zero blocks: **the pack parsed clean, raised nothing, and returned an
empty document.** The defect the docstring named, sitting beside the guard
written against it.

**Why:** a loud failure is the one you can picture, so it is the one you guard.
The silent failure has no symptom to imagine — it looks like a successful read
of an empty thing — so it does not present itself as a case to handle. Writing
the principle down does not surface the instance; only enumerating the failure
modes does. Worse, the artifact here was a *probe*, and a probe returning zero
is indistinguishable from a probe finding nothing — this project had already
been burned by exactly that, counting zero SDT packs three times before a human
opened two PDFs.

**How to apply:** before shipping a parser or validator, list every way the
input can be wrong and mark which ones produce *no exception* — an empty
result, a zero count, a default. Those are the guards worth writing; the ones
that crash will be found in a week anyway. Where the format has an upstream
validator, port it rather than inventing your own contract: mirroring
`validateIndexShape` covered corruptions my own tests never named (non-monotonic
middle entries, `byte_offsets` damage), which the reviewer found by attacking
vectors I had not thought of. And prove each new guard's test fails against the
*unguarded* code — see [[feedback-verify-the-load-bearing-claim]]; that control
is what made the fix credible rather than merely asserted. Related:
[[feedback-a-move-can-leave-the-gate]].
