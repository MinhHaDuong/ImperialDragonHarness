---
name: feedback_static_guard_cannot_replace_an_invariant
description: "A guard that pattern-matches source text is always one spelling behind; when the property is checkable at runtime, assert the property"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-28T08:33:15.752Z
---

A guard that reads source text to forbid a defect can only forbid the spellings
you thought of. If the thing you actually care about is a *property of the data*,
assert the property.

Ticket 0402 (2026-07-28) escalated through three rounds of this:

1. A regex forbidding `fillna(2020)`. Review broke it with `fillna(2020.0)`,
   `fillna(value=2020)`, `fillna(CURRENT_YEAR)`, and an `np.where`.
2. An AST check — better, since every one of those collapses to the same tree.
   Review broke it two ways: fabricating *before* the parse
   (`df["year"].replace("", "2020")`, after which the corpus looks legitimately
   dated and every later check is vacuously true), and routing a parallel column
   into the helper (`s2["eff_year"] = s2["year_num"].replace(np.nan, 2020)`).
3. Runtime invariants, which is what finally held.

Two traps inside the fix itself, both paid for:

- **Where you take the measurement is the whole guard.** Counting blanks *inside*
  a `parse_years(raw)` wrapper looks equivalent to counting them at the read and
  is not: the wrapper receives the already-fabricated column, so its count agrees
  with itself. The read and the count must sit in one function that nothing can
  get between (`read_corpus_with_years`).
- **Check the authoritative column, not the argument.** An invariant inside a
  helper is vacuous when the caller passes a parallel column with the gaps
  pre-filled. Assert on the frame's own `year_num`.

Runtime and static are complementary, not ranked. The one route no runtime check
can see is reassigning the column *after* the guarded read — it leaves no undated
row for an invariant to find, and only the AST provenance check catches it. So
two layers abort a real run and the third fails `make lint`.

**How to apply:** when writing a guard, ask whether the defect has a data
signature. If yes, assert it in the code path (it costs nothing and holds however
the caller was written) and keep the static check for routes that erase the
signature. And never write "unbypassable" in a commit message — I did, and it was
false within one review round (→ [[feedback_check_the_detector_first]]).

**Why:** the guard is the deliverable's warranty. A green guard that a two-line
edit defeats is worse than no guard, because it is *believed*.
