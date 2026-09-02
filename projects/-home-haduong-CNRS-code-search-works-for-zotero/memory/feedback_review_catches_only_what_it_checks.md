---
name: feedback-review-catches-only-what-it-checks
description: "An independent review pass verifies what it's scoped to check; a genuinely different question from the author found a defect two review passes missed"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1be9e24-a4bf-4649-91f5-e30e88656d14
  modified: 2026-09-01T08:31:27.845Z
---

Self-review and an independent decorrelated review (Fable 5, fresh context)
both passed a draft upstream comment on citation accuracy and number
accuracy, line by line. Neither caught that one sentence implied zoteus
already had an `auto` execution-provider/device setting — it doesn't; the
phrase was carried over unnoticed from this repo's own internal benchmark
harness, which does have one. The defect surfaced only when the author asked
"does this move open GPU acceleration?" — a genuinely orthogonal question
neither review pass had been pointed at.

**Why:** a review checks what its prompt tells it to check. "Verify every
citation and number against source" is a real, narrow instrument — it will
not notice a claimed *concept* (a config knob, a setting, a mechanism) that
was never verified to exist in the target codebase at all, because nothing
asked it to. Two passes of the same instrument compound thoroughness on the
same axis; they don't add a new axis.

**How to apply:** when reviewing a document making claims about an external
system (source citations, upstream precedent, config surfaces), the review
prompt should explicitly include "does every named setting/mechanism/concept
actually exist in the source, not just the numbers and line citations" —
grep the target source for it, don't just check that adjacent claims are
line-accurate. And treat a stakeholder's own question, even one framed as
curiosity, as a review pass in its own right: it exercises whatever axis they
happen to ask about, which is not necessarily the axis the last review
covered. See also [[feedback_probe_needs_discriminating_control]].
