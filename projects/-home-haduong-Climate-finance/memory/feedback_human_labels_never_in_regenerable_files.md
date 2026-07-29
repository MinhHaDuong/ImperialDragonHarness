---
name: feedback_human_labels_never_in_regenerable_files
description: A generator that writes a fill-me-in column destroys the filled copy on its next run; human annotations need an append-only artifact the pipeline can never overwrite
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 11b8660f-8b9e-4d0b-abc1-cab92ed4f30f
  modified: 2026-07-28T09:15:50.993Z
---

The data paper's AUC = 0.818 human validation became unverifiable because the
100 per-work labels were stored in the file that collected them:
`compute_reranker_calibration.py` writes `hitl_df["human_label"] = ""` ("to be
filled by reviewer") into `docs/reranker_hitl_stratified.csv`, the author
graded the working-tree copy in place, and a later re-run regenerated the
sheet blank. Every surviving version is empty; only aggregate quintile rates
in a tech-report paragraph survived (ticket 0372, forensics 2026-07-28).

**Why:** "fill this generated file and re-run" makes the annotation's only
home a file the pipeline owns. Any rebuild — a Make dependency firing, a
fresh worktree, a config tweak — silently destroys irreplaceable human work.
The loss is invisible: the file still exists, same name, same schema.

**How to apply:** human judgments (grades, adjudications, panel votes) go in
their own append-only artifact keyed by (item, annotator), written by a
dedicated writer that refuses to overwrite existing rows — never as a column
in a regenerable sheet. If a collection sheet must be generated, the
generator aborts when the target exists with non-empty annotations (0585
files the guard; 0541's panel protocol carries the append-only invariant).
When auditing a validation claim, check where its labels *live* before
trusting that they still exist.

Related: [[feedback_regenerate_dont_merge_generated]],
[[feedback_assert_on_written_artifact]].
