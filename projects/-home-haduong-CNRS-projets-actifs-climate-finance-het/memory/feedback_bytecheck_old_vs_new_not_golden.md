---
name: feedback_bytecheck_old_vs_new_not_golden
description: "Byte-check a behavior-preserving refactor by running old code vs new code on the SAME current data, never against a committed/main-checkout golden (which drifts with the corpus)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e7152bef-44bf-4bb6-b335-75a112d71036
---

To verify a behavior-preserving refactor (e.g. migrating a script's contract
read to a loader, ticket 0199) preserves figure/table bytes, compare **old code
vs new code on the same current data** — not the new output against a "golden"
copy in the main checkout or git.

**Why:** Phase-2 figures/tables (`content/figures/`, `content/tables/`, `*-vars.yml`)
are gitignored regenerable artifacts. The copy sitting in the main checkout was
generated from whatever corpus snapshot existed *then*; the current
`refined_works.csv` has since drifted (0199 case: golden had 31713 refined rows,
current data 30987). A diff-vs-golden therefore conflates **data drift** with the
**code change** and reports a false "DIFFERS".

**How to apply:** regenerate with the migrated code to a temp path; then
`git show origin/main:scripts/<x>.py > scripts/<x>.py` (overwrite), regenerate the
OLD version to a second temp path, `git checkout HEAD -- scripts/<x>.py` to restore,
and `md5sum` the two temp outputs. Identical ⇒ migration is byte-preserving. Point
`CLIMATE_FINANCE_DATA` at the main checkout's `data/` so a fresh worktree (no DVC
data) can run the scripts read-only. This proved all four 0199 offenders
byte-identical, including the `plot_fig1_bars` year `Int64`→`float64` coercion the
ticket flagged as a risk. Relates to [[feedback_manuscript_number_provenance]]
(only archived pipeline numbers) and [[feedback_stale_worktree_make]].
