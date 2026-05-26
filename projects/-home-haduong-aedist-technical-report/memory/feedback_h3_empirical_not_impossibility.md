---
name: H3 must use empirical language, not impossibility claims
description: H3 says "does not" (empirical observation on SOTA), never "cannot" (impossibility claim) — applies to all docs and code
type: feedback
originSessionId: a8674d80-1e78-499e-aa96-f5a6a8574fb9
---
H3 claims an empirical trade-off on current SOTA systems, not a logical or architectural impossibility. Use "does not simultaneously achieve" or "does not provide" — never "cannot" or "is incompatible with."

**Why:** User flagged "cannot simultaneously achieve" as over-generalization during 2026-05-06 session. "Cannot" implies impossibility in principle; H3 is an observation about current state-of-the-art systems that may change as models improve.

**How to apply:** In `docs/synopsis.md`, `docs/hypotheses.md`, `docs/preregistration-osf.md`, slide text, and any future paper draft — always use "does not" language for H3. H3 title: "Accuracy–provenance trade-off in single parametric prompts" (not "incompatibility").
