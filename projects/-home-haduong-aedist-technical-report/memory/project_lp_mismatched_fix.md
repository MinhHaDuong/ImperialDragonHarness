---
name: project-lp-mismatched-fix
description: "LP Mismatched rows were mis-routed to EXACT_CAPACITY_DIFF, inflating tp; fixed in PR"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0b55f32e-04c2-413c-be58-8e82a63101f9
---

LP reconciler had a bug: rows where LP forced a below-threshold pairing (status "Mismatched") were caught by the `else` clause in `_extract_entries()` and routed to `MatchType.EXACT_CAPACITY_DIFF` (a matched type), inflating tp across all models.

Fix (PR #547, merged 2026-05-25): explicit `elif status == "Mismatched":` emits two separate entries — REFERENCE_ONLY + SYSTEM_ONLY — and continues. The else clause now only catches genuine "(Diff)" variants.

Also fixed in same PR: đ (U+0111) not stripped by NFD pass; single-unit suffix " 1" stripped for 5 known single-unit plants from golden reference.

**Why:** LP cost structure (mismatch_penalty=1000 << dummy_cost=10000) guarantees every record gets paired; "Mismatched" is the LP's honest label for below-threshold forced pairs.

**How to apply:** When reading evaluation metrics pre-2026-05-25, treat tp/f1 as inflated. Post-fix measurements.jsonl is authoritative.
