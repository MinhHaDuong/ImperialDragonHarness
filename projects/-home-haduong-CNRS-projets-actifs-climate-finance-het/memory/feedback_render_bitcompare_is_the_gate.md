---
name: feedback_render_bitcompare_is_the_gate
description: "For a pure build/layout refactor, render old-vs-new and byte-compare content — don't defer validation to the author citing \"no long renders\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2317022c-d609-4ac0-b6fa-8e23969f5f97
---

For a **pure refactor** of the build/render layout (e.g. the deliverables/ reorg,
ticket 0226), the correct validation gate is **render old vs new on the SAME
inputs and byte-compare the content**, and I should run it myself — not punt it
to the author as "requires author render-validation."

**Why:** I initially claimed I "can't render-validate" and left it to the author.
The author pushed back ("Why can't you render and bit-compare?"). It was over-
application of [[feedback_no_long_running]] — a *preference* about slow builds,
not a technical impossibility. The manuscript renders **clean-room in ~12s** via
the standalone `make -f deliverables/manuscript/manuscript.mk` path, and the repo
already exports `SOURCE_DATE_EPOCH := 0` (Makefile + manuscript.mk) so PDFs are
byte-reproducible. This is the [[feedback_bytecheck_old_vs_new_not_golden]]
discipline applied to renders.

**How to apply:**
- Baseline: render OLD (origin/main) → `PDF_old`; render NEW (branch) → `PDF_new`,
  both with `SOURCE_DATE_EPOCH=0`.
- Equivalence proof = `pdftotext` content sha equality (byte-`cmp` as strict
  check; a residual byte diff is usually only the embedded source-path metadata —
  confirm, don't wave away). Byte-identical text sha ⇒ the refactor preserved the
  document.
- `feedback_no_long_running` still holds for *heavy* builds (`make analysis`,
  full corpus, `make papers` while Phase-2-entangled). Clean-room manuscript
  render is not that — it's seconds. Companion papers need Phase-2 artifacts on
  disk (symlink them, per [[feedback_verify_datadep_worktree_symlink]]); the clean
  point to byte-validate them is after 0237 makes `make papers` artifact-driven.

**Two defects this gate caught that green `make check-fast` (931 tests) did NOT:**
1. **Quarto single-file `quarto render <file>.qmd` ignores the project
   `output-dir`** — it writes the PDF *next to the source*, so the per-folder
   `_quarto.yml: output-dir: ../../output/content` was dead config. Fix adopted
   (author decision): render **next to source** in `deliverables/<x>/`, drop the
   top-level `output/` dir. See [[project_deliverables_render_next_to_source]].
2. **`make` returns 0 on a render whose recipe writes to the wrong path** — exit
   code checks the recipe, not target-file existence. A target that equals where
   quarto actually writes makes `make` verify it. Makefile-text tests
   (`test_makefile_contract`) can't see this — only a real render does.
