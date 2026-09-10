---
name: feedback-walker-covers-one-tier-of-two
description: "memory is two-tiered — projects/*/memory and the promoted memory/ — and a glob written for one silently exempts the other; three instances in one session, two in new code"
metadata:
  type: feedback
---

# A glob for `projects/*/memory` is half a walker

Harness memory has two tiers: `projects/<slug>/memory/` per project, and
`memory/` for entries promoted across projects. Both are resident — the runtime
injects the project index, `scripts/on-start.sh` prints the harness one. Code
written for "the memory tree" reaches for `projects/*/memory` and stops there.

Three instances on 2026-09-10, **two of them in code written that same day to
fix the first**:

1. `test_rules_resident_budget.py` capped `rules/` while being read as the gate
   on the whole resident preamble.
2. Its replacement globbed `projects/*/memory/MEMORY.md` and left the harness
   index ungated.
3. `provenance.py`'s coverage walker did the same, leaving a live promoted
   entry with no record at all — invisible to the check whose subject is
   invisibility.

**Why:** the failure is self-similar. Each fix was written by someone who had
just been bitten by the previous one, and reproduced it anyway, because the
project tier is where the files obviously are and the harness tier is four
files in a directory you do not scroll past.

**How to apply:** when touching anything that walks memory, name both roots in
the same expression and let the caller pass the checkout root rather than
resolving from `Path.home()`. Then check the *other* sites: on 2026-09-10 the
sweep found `scripts/pretooluse-worktree-path-guard.sh` exempting
`projects/*/memory/*` and not `memory/*`, and `/dream` never consolidating the
harness tier at all. Both below the severity floor, both the same shape.

Not a candidate for a mechanical guard: `scripts/resident_census.py`
legitimately globs one tier because it counts the other in a different channel,
so a grep-based class test would misfire on correct code.

See also [[reference_no_recall_channel_fires]], [[feedback_measure_whether_a_guard_ever_fired]].
