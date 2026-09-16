---
name: feedback_split_contract_needs_parity
description: Splitting one contract into two structures needs an explicit key-set assertion; the silently-wrong direction is the one that bites
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 607f3a3f-6d91-4d8f-9a57-a21a50b89615
  modified: 2026-07-28T08:39:22.155Z
---

When a refactor splits one contract into two parallel structures keyed by the
same entity, add a parity assertion in the same commit. Do not rely on the
consumer to notice a mismatch — check whether it *can*.

**Why:** Ticket 0357 (2026-07-28) split a document registry into
`DOC_VARS` (document → variable names) and `DOC_VARS_FILE` (document → output
path), both in `scripts/analysis/_vars_registry.py`. Parity held on the day, and
nothing enforced it. Two reviewers flagged it independently, which is what made
it worth acting on rather than noting.

The reason it is worth a test and not a comment is that the two failure
directions are **asymmetric**:

- A document in `DOC_VARS` with no `DOC_VARS_FILE` entry raises a bare
  `KeyError` from three call sites. Loud, if cryptic. Survivable.
- The mirror — a path declared for a document the variable registry never
  lists — is *silently never written*. The document then renders `?meta:`
  placeholders and the build exits 0.

That second case is the exact defect the ticket existed to remove, arriving
again by a different route. A split that can reintroduce the bug it was part of
fixing is the shape to watch for.

**How to apply:** After splitting a mapping, ask which direction of divergence
throws and which one silently degrades. If either is silent, assert
`set(A) == set(B)` and red-test it *both ways* — dropping an entry from each
side in turn. One-directional mutation testing passes a guard that only checks
one subset relation. Look for the same shape wherever a Makefile variable list
mirrors a Python list, a config section mirrors a schema, or an allowlist
mirrors an enum.

Related: [[feedback_guard_the_class_not_the_stale_value]],
[[feedback_red_test_the_guard_you_wrote]],
[[feedback_renderer_placeholder_exit_zero]] (the exit-0 placeholder this
registry exists to prevent).
