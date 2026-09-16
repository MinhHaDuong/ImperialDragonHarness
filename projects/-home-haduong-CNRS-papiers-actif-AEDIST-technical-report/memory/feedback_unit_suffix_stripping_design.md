---
name: feedback-unit-suffix-stripping-design
description: "Unit-suffix stripping must use the fixed golden reference, not dynamic DataFrame content"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0b55f32e-04c2-413c-be58-8e82a63101f9
---

Strip trailing " 1" from single-unit plant names using a set pre-computed from the fixed golden reference — not dynamically from whatever DataFrame is passed in at runtime.

**Why:** The first implementation computed uniqueness from the input DataFrame. One-sentence correction from user: since the reference is fixed, the eligible set is fixed too. Dynamic computation gives inconsistent behaviour depending on what the model output contains.

**How to apply:** Any per-string or per-dataset normalisation that depends on "what other records exist" should derive its rule from the authoritative fixed source (the reference), computed once at module load, not from the current input.
