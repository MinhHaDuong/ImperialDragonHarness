---
name: feedback_or_empty_does_not_catch_nan
description: "`str(x or \"\")` and `row.get(k, \"\")` both fail on a pandas NaN — NaN is truthy and the key is present — so the two commonest null guards in this repo are inert exactly where they are needed"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c005a06f-79a6-403f-9684-c3dbe29124f2
  modified: 2026-07-28T08:10:20.588Z
---

Two idioms that read as null guards and are not, both live in this repo's
pipeline:

```python
row.get("title", "")          # key IS present, holding NaN -> returns nan
str(row.get("title", "") or "")   # float('nan') is TRUTHY -> returns 'nan'
```

`str(nan)` is `'nan'`, so both ship the literal three-letter string. They work
only when the missing value is `None`; `pd.read_csv` produces `NaN`.

Measured, not reasoned about (2026-07-28): a `None` cell yields `''`, a real
`NaN` cell in an object column yields `'nan'`. The distinction is the whole
trap — a test written with `None` passes while production fails.

**Why it hides:** the `or ""` *looks* like it handles the case, so a reader
checking for a null guard finds one and moves on. Ticket 0375 fixed one
`row.get` site; the roar sweep then found **52** occurrences of the `or ""`
variant across 13 files, plus 30 bare `str(row.get(...))` (ticket 0550).

**How to apply:**

- Blank on `pd.isna(v)` explicitly, once per function, *before* any formatting
  — not beside the branch that happens to need it today. In `_write_md_table`
  the null check sat next to the int-formatting branch, so only three of eight
  columns were covered and the next column added inherited the hole.
- One shared helper beats N hand-edits: 52 call sites is 52 chances for the
  semantics to drift.
- **Grep the shipped artifact for the token with a word boundary**, never
  `"nan" in text`. The corpus-sources caption contains "prove**nan**ce", so the
  naive check fires on correct output — a check that cannot distinguish its pass
  from its failure. That near-miss was caught only by running the sweep against
  the real shipped table.

Related: [[feedback_nullable_blank_passes_the_schema]] (a coerced blank
validates cleanly where the column is nullable — same class, one layer down),
[[feedback_assert_on_written_artifact]], [[feedback_check_the_detector_first]].
