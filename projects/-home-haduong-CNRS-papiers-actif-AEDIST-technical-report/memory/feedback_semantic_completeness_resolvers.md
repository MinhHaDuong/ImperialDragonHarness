---
name: feedback-semantic-completeness-resolvers
description: "When a function resolves identifiers to a category (model → family, slug → color), pin completeness against live data, not just hand-crafted examples."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f6f1d1a2-4c3d-4e54-b814-4c59988b5ad0
---

When building a resolver that maps identifiers to a category — `family_color(model)`, `model_family(slug)`, or any similar lookup — unit tests over hand-crafted inputs cover the API but miss the empirical question: *does every identifier actually present in the data resolve to a non-fallback value?*

**Why:** PR #380 (ticket 0194) shipped `family_color()` with 9 unit tests covering EN/FR/ZH cross-family, fallback, prefix-stripping, etc. All passed. `/verify` still caught a blocker: `cogito:8b` and `granite3.3:8b` (locally-served via Ollama) hit the fallback gray because they weren't in the provider_map OR the slug_prefix_map. The hand-crafted tests never tried any real measurements-side model.

**How to apply:** When a PR adds or modifies a resolver, the test suite should include a **parametric test that iterates every distinct identifier appearing in `measurements.jsonl`** (or the comparable production data source) and asserts non-fallback resolution. This is cheap (one loop, one assertion) and catches the entire class of "I forgot about model X" gaps.

Pattern:

```python
def test_every_model_in_measurements_resolves_non_fallback():
    from aedist.measurements import load
    slugs = {r.method_params.model for r in load()}
    for slug in slugs:
        assert family_color(slug) != _LANG_FALLBACK, slug
```

Not yet added to the project — file a ticket if you see another such gap. The complementary [[feedback-csv-writer-fieldnames]] pattern (assert keys match) is the same shape: cheap mechanical completeness check against actual data.
