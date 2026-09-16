---
name: feedback_pin_known_defect_not_xfail
description: Recording a known defect as xfail is content-blind — a second defect in the same target reports the identical xfail; pin the exact expected set so the guard fails in both directions.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 865fbacb-7066-4c68-8060-1935f1783217
  modified: 2026-07-27T19:17:19.109Z
---

When a new guard finds a real defect whose fix belongs to another ticket, the
reflex is `pytest.mark.xfail(strict=True)`. It is the wrong instrument. An
xfail asserts only *that* the target fails, so a **second, unrelated defect in
the same target reports the identical `1 xfailed`** and nothing notices. The
one place with a deferred fix becomes the one place a fresh defect can hide —
and it hides for exactly as long as the exemption lives.

Pin the expected set instead, and assert equality.

**Why:** ticket 0363 (2026-07-27). A guard over Quarto's `?meta:` placeholders
found `corpus-report` rendering 12 unresolved keys, with the fix deferred to
another ticket pending a Phase-2 regeneration. Recorded first as a strict
xfail; a review round proved by mutation that planting a *new* unresolved key
there changed nothing observable. Replaced by `KNOWN_UNRESOLVED = {doc:
frozenset(the 12 keys)}` with the guard asserting equality, verified in both
directions: adding a bogus macro fails with "1 key(s) nothing declares", and
declaring one of the twelve fails with "1 key(s) now resolve — drop them from
KNOWN_UNRESOLVED".

**How to apply:**
- **Equality, not emptiness.** `assert unresolved == expected`, where `expected`
  is `frozenset()` for healthy targets. One code path covers both, and the
  failure message should name the two directions separately: keys newly broken,
  and keys now fixed that should be removed from the registry.
- **It self-destructs correctly.** When the other ticket lands, the set empties,
  equality fails, and whoever fixed it deletes the entry — the same property
  `strict=True` is reached for, without the blindness.
- **Watch the skip interaction if you do keep an xfail.** A `pytest.skip()`
  raised inside `xfail(strict=True)` reports SKIPPED, not XPASS, so a guard that
  can skip — anything needing a toolchain or a generated artifact — cannot be
  relied on to self-destruct at all.
- Applies well beyond rendering: any registry of known-failing targets
  (allowlists, expected-lint-failures, quarantined tests) has this shape. See
  [[feedback_renderer_placeholder_exit_zero]] for the case that produced it.
