---
name: feedback_derived_token_figures_must_be_swept
description: A token count divided out of a character count is derived, not measured; /context is the only local token measurement, and correcting such a figure means sweeping every copy — one lived inside the resident set itself.
metadata:
  type: feedback
---

Characters are exact and cheap to count. Tokens are not, and no local
tokenizer exists here — neither `tiktoken` nor the `anthropic` SDK is
installed, so `count_tokens` is unavailable. What filled the gap for years was
`chars // 4`, written into the rules budget guard, the README, STATE.md and
`scripts/trace-digest.py`.

Dividing `/context`'s own per-category totals by a character census of the same
files gives **2.76 chars/token** on the memory-files channel and **2.98** on
the skills channel — two independent categories agreeing, which is the only
reason a single constant is defensible. `chars // 4` therefore understates this
corpus by about 45%: the rules tree costs ~12 800 tokens, not the ~8 800 that
three files recorded. Backticked identifiers and paths tokenize far worse than
prose, which is why a generic rule of thumb fails here specifically.

**Why:** a number obtained by dividing reads like data and carries none of the
error bars of the aggregate it came from. The budget for the resident set was
being argued on a figure that was optimistic by half, and nothing in the repo
said the figure was derived.

**How to apply:** label a derived quantity as derived, show the arithmetic, and
name the measurement it came from — `scripts/resident_census.py` does this in
its module docstring and re-derives on demand. Then **sweep every copy**: the
correction pass that fixed `README.md` left the same stale `~8 800` in
`rules/README.md`, which is *resident in every session of every project*, and
left `total // 4` in the failure message of the very guard being corrected.
Both were found by a `/roar` sweep against `origin/main`, not by the PR's own
review. `scripts/trace-digest.py` still divides by 4 deliberately: its corpus
is conversation text, and changing it would break the comparability of every
`/trace-doctor` series.

Related: [[reference_rules_tree_is_resident]],
[[feedback_measure_whether_a_guard_ever_fired]].
