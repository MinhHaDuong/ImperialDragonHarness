---
name: feedback_hardcoded_secondary_path_survives_input_gate
description: "a script's primary --input gate can hide a hardcoded secondary-file path bug that only shows up once the harness actually reaches that code"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9770a739-750e-4861-87af-5e34db64916e
---

When a Phase-2 plot script accepts `--input` for its primary CSV but reads a
secondary co-located file (e.g. `cluster_labels.json` written by the same
producer to the same `--output` dir) via a hardcoded `DERIVED_TABLES_DIR`
constant instead of deriving it from `--input`'s directory, the bug is
invisible until the harness actually exercises that code path — a broken
launcher (ticket 0262: `SCRIPTS_DIR`/`REGISTRY` path rot from the 0240
scripts/ reorg) can mask it indefinitely by preventing Wave 2 from ever
running to completion.

**Why:** fixing ticket 0262's stated scope (launcher paths only) let Wave 2
run for the first time in this harness, which immediately surfaced two
independent instances of this shape in `plot_fig_alluvial.py` and
`plot_fig2_composition.py` — one crashed (`FileNotFoundError`), the other
silently fell back to placeholder `"Cluster N"` labels via
`load_cluster_labels()`'s warn-and-fallback path, which is worse: it doesn't
fail loud, it bakes wrong content into a "passing" golden hash. A grep sweep
for the same shape (`--input`-gated primary + unconditional
`DERIVED_TABLES_DIR` secondary) across `scripts/figures/*.py` found a third,
still-unfixed instance in `plot_ncc_alluvial.py` (not in `REGISTRY`, so
un-exercised by the regression suite) — filed as ticket 0265 rather than
fixed inline, to keep 0262 atomic.

**How to apply:** when a path-relocation or launcher fix suddenly lets a
previously-never-completing test path run for the first time, treat any
resulting failures as potentially pre-existing and unrelated to the
relocation itself — verify by reverting just the specific behavioral fix and
confirming the crash/mismatch reproduces on the "unrelated" pre-existing
code. When you find one instance of "properly `--input`-gated primary read +
hardcoded secondary read," grep sibling scripts for the same co-occurrence
(`io_args.input` + `DERIVED_TABLES_DIR` in the same file) — this shape tends
to repeat across near-duplicate companion scripts (`plot_fig_alluvial.py` /
`plot_ncc_alluvial.py`). See [[project_file_relocation_move_surface]].
