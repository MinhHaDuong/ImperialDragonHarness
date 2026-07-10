---
name: feedback_pin_test_mutation_teeth
description: "A regression-pin test passes on current behavior; prove its teeth by mutating the guarded mechanism, and quantify a suspected inefficiency before refining it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0b7a45f-2dcb-4c20-8ce2-d23009542820
---

Two techniques from ticket 0228 (hardening the fast-path heavy-import auto-mark).

**A regression PIN has no natural red step — mutate the mechanism to prove teeth.**
A pin test (e.g. "pytest fires user `pytest_collection_modifyitems` before its `-m`
deselection, so an auto-added `slow` marker deselects the test") passes on the
current codebase because the behavior already holds — there is no failing-first
state from writing production code. So the honest TDD red is a *mutation*:
temporarily break the guarded mechanism (disable the `add_marker` call in the
synthetic conftest), confirm the pin fails, then revert. Without this a pin can be
a tautology that never catches the regression it claims to. Gotcha: `git checkout
-- <file>` cannot revert an *untracked* new test file — restore the mutation with
an explicit Edit, or commit first.

**Quantify a suspected inefficiency before refining its granularity.**
The ticket assumed module-granularity auto-marking "over-swept" ~95 tests off the
fast path and asked whether per-test refinement was worth it. *Measuring* reframed
the decision: ~85% of the swept tests were heavy-*compute* modules
(`test_null_model` etc. — timed out >55s even with the heavy import excluded) that
the layer-2 duration ratchet excludes anyway, and another module imported the heavy
dep at top level (unrecoverable). Only ~12 genuinely-light tests were recoverable —
not worth a fragile per-test call-graph detector. The suspected waste was largely
illusory. Time the exemplars before optimizing; the numbers, not the intuition,
decide. Relates to [[feedback_manuscript_number_provenance]] (cite measured, not
assumed, numbers).
