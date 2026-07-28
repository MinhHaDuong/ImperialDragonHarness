---
name: feedback_nullable_blank_passes_the_schema
description: A schema on the written artifact cannot catch a value silently turned into a blank in a nullable column — the write step must refuse it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-27T19:15:25.496Z
---

Validating the written artifact catches far more than a frame-level assertion
(→ [[feedback_assert_on_written_artifact]]), but it has one blind spot worth
knowing: **a value silently converted to empty in a column the schema declares
nullable validates cleanly.**

Concretely (ticket 0354, 2026-07-27): `export_deposit.coerce_integer_columns`
used `pd.to_numeric(..., errors="coerce")`, so a malformed year (`"n.d."`)
became an empty cell. `year` is `nullable` — measured, because the shipped data
genuinely has gaps — so `frictionless validate` reported the deposit VALID while
the value was gone. The descriptor could not have caught it at any strictness:
`required` is false by measurement, and that measurement is correct.

The fix belongs at the write step, not in the schema: `errors="raise"`. Genuine
gaps arrive as NaN from `read_csv` and pass through untouched; only a *value that
failed to parse* raises.

**How to apply:** whenever a coercion feeds a column the schema lets be null,
ask what happens to a malformed value. If the answer is "it becomes a blank",
the schema is not your gate — make the coercion strict. Measure first: on the
current corpus all four integer columns had zero coercion losses, so strictness
cost nothing. The same question applied to `errors="coerce"` across `scripts/`
found `build_het_core.py` doing worse — `.fillna(2020)` *invents* a year that
feeds a ranking score (ticket 0402).

**Why:** the deposit's whole premise is "publish nothing a validator cannot
check". A silently-emptied value is a claim the validator structurally cannot
check, so it needs a different mechanism rather than a stricter descriptor.
