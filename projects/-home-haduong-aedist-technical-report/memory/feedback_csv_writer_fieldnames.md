---
name: DictWriter fieldnames must match all row keys
description: When adding fields to a row dict, always update the DictWriter fieldnames list in the same edit — and update the corresponding test assertion
type: feedback
originSessionId: 1eac4591-b38f-4d1d-baa4-84728e2bb3d7
---
When `load_convergence_data()` or any loader adds new keys to row dicts, the `csv.DictWriter(f, fieldnames=[...])` list must be updated in the same commit. The writer raises `ValueError` silently-at-runtime if rows contain keys not in fieldnames.

**Why:** PR 296 introduced `local` and `size_class` to rows but left the old fieldnames list — the test caught it on review, not at commit time.

**How to apply:** Always grep for `DictWriter` near the function that builds rows. Update both the writer and the test assertion for `reader.fieldnames` in the same edit.
