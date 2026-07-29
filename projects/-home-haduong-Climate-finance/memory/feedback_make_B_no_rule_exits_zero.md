---
name: feedback-make-b-no-rule-exits-zero
description: "`make -B <target>` exits 0 without building when the target's rule lives in a makefile the root does not include — an A/B regeneration check then compares a file against itself and reports no churn"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c005a06f-79a6-403f-9684-c3dbe29124f2
  modified: 2026-07-28T07:30:48.369Z
---

`make -B <target>` does **not** guarantee the target was rebuilt. When no
loaded makefile has a rule for it, Make treats the existing file as up to date,
prints `Rien à faire pour « <target> »` / `Nothing to be done for '<target>'`,
and **exits 0**. An A/B regeneration check built on that invocation then copies
the same untouched file twice and reports "byte-identical — no churn".

Concrete (ticket 0376, 2026-07-28). The no-churn check regenerated all nine
targets from `tests/_mk_discovery.generated_markdown_targets()` under old and
new versions of the Markdown escaper. Eight rebuilt. `tab_venues_fr.md` did
not: its rule lives in `deliverables/manuscript/manuscript.mk`, the Phase-3
clean-room render makefile, which the top-level `Makefile` deliberately does
**not** `-include`. Rebuilt properly with
`make -B -f deliverables/manuscript/manuscript.mk <target>`, it was genuinely
identical — but that was luck, not the check working.

**Why it hides:** this is the general trap that "an all-clear indistinguishable
from *I could not look* is not a check", in Make's clothing. Exit 0 plus an
unchanged file is exactly what a real pass looks like. The discovery surface
was right — it listed all nine — so the enumeration step gave no warning; the
failure was one layer down, in the *build* step.

**How to apply:**

- After a forced rebuild, prove the file was written: diff `stat -c '%Y'`
  before and after, or delete the target first and assert it reappeared. Do not
  infer the build from make's exit code.
- Grep for the target across `*.mk` before assuming the root Makefile owns it.
  This repo splits Phase-3 render rules into per-deliverable `.mk` files that the
  root does not include, by design.
- The mtime discipline is the same one that proves a leak stopped
  ([[feedback_mtime_not_content_for_leaks]]): idempotent writes keep content
  identical, so content can never prove a write happened.

Related: [[feedback_stale_prerequisite_masks_missing_artifact]] (drifted
prerequisites fail open the same way), [[feedback_corpus_rerun_byte_compare]],
[[feedback_enumerate_from_the_surface_not_the_diff]],
[[feedback_gh_pr_list_files_empty]] (same "could not look" shape, different tool).
