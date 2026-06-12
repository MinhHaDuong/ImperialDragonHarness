---
name: feedback-pydantic-unknown-kwargs
description: "Pydantic BaseModel in this repo accepts unknown kwargs silently — design schema tests around the *effect*, not the *literal* the constructor accepts."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1e258e6e-d360-4400-8ca6-db7dad9f7e44
---

When writing tests for `RunRecord` / `ResourceUse` schema extensions in
`src/aedist/schema.py`, do not assert "field present with default value" —
Pydantic accepts unknown kwargs without raising (model_config does not
set `extra="forbid"`), so a test like `assert m["new_field"] is None`
silently passes against a model that doesn't actually declare the field.

**Why:** A Phase-5 agent on ticket 0172 (2026-05-14) discovered the
first-failing test would have passed on `KeyError: 'n_web_search_calls'`
in the metrics dict rather than on the constructor when the field
didn't exist — so the test caught the right bug but for the wrong
reason.

**How to apply:** Test the *projection effect* in `records_to_metrics()`,
not the construction. Use asymmetric values (e.g. `len(web_search_calls)
== 3` vs `len(citations) == 2`) so the assertion only passes when both
projections are wired correctly and distinctly. Same shape applies if
we ever flip `extra="forbid"` — at that point construction tests
become meaningful, but until then, projection tests are the load-
bearing assertion.
