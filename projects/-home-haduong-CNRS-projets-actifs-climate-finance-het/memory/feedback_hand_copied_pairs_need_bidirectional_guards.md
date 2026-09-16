---
name: feedback_hand_copied_pairs_need_bidirectional_guards
description: A "must match" comment on hand-copied pairs is a confession, not a guard; assert equality both directions and red-test each direction separately
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f6a59d05-fc03-4ef4-8906-2e4ae1c5323b
  modified: 2026-07-28T18:03:21.075Z
---

Ticket 0571 (PR #1269, 2026-07-28) found three unrelated pairs of structures
that each carried a "must match" comment and nothing enforcing it: the band
scheme (`N_COMMUNITIES`/`BAND_NAMES`/`BAND_COLORS_RGB`, hand-copied into two
renderers), `DEFAULT_THRESHOLDS` vs `config/analysis.yaml`, and
`ZOO_SCHEMATIC_STEMS` vs the scripts actually on disk. Every divergence was
silent — no exception, no missing target, wrong or absent output at exit 0.

**Why the comment is a tell, not a fix:** someone already saw the drift risk
and wrote it down instead of enforcing it. Grepping a codebase for `# must
match`, `# keep in sync`, `# mirrors`, or similar phrasing finds the guard's
own admission of the gap it should have closed — a cheap sweep with a high
hit rate (this ticket's own sweep found the three above from one pass).

**Why one direction is not enough:** `ZOO_SCHEMATIC_STEMS` vs the glob is the
sharpest case. The original code only checked "every declared stem has a
script" — loud when violated. It missed "every script has a declared stem" —
a script with no stem is simply never built, and `make zoo-figures` ships the
deliverable one panel short, at exit 0. Same asymmetric-direction shape as
`feedback_split_contract_needs_parity`, generalized beyond one ticket's
split-contract case to any pair a human is expected to keep in sync by hand.

**How to apply:**
1. Grep for "must match" / "keep in sync" / "mirrors" comments — each one is
   a candidate guard.
2. For each pair, write the equality check both directions:
   `only_in_a = a - b; only_in_b = b - a`, fail loud on either being
   non-empty, name the actual missing/extra elements in the message.
3. Red-test both directions separately by injecting a one-sided divergence
   (add to A only, then add to B only) — a guard that only fails one way
   passes a mutation test that should catch it. Reference test:
   `tests/test_zoo_mk.py` (generalized to take the variable name so
   `CROSSYEAR_METHODS` and `ZOO_SCHEMATIC_STEMS` share one regex).
4. For a config-vs-code default pair specifically, also assert the config
   *block itself exists* — a renamed or deleted block should not silently
   fall back to the code default via `{**DEFAULTS, **cfg}` merge order.

**Known residual (filed, not fixed):** the AST guard that checks band-scheme
*re-definition* does not catch *re-binding* — `BAND_COLORS_RGB[0] = "..."` in
a consumer module still forks the shared state at runtime with no failing
test. Ticket 0593 tracks making the shared constants immutable
(`MappingProxyType`) to close that. Same defect class, one layer down.

Related: [[feedback_split_contract_needs_parity]],
[[feedback_guard_the_class_not_the_stale_value]],
[[feedback_red_test_the_guard_you_wrote]],
[[feedback_renderer_placeholder_exit_zero]].
