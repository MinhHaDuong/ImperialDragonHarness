---
name: feedback_verify_datadep_worktree_symlink
description: "Validate a data-dependent Makefile/Phase-2 change in a worktree by symlinking the primary checkout's contract files, then building the affected targets"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f6a48638-2613-4ecf-8fa8-1ce04f654b82
---

A worktree has the committed `.dvc` pointers under `data/catalogs/` but not the
materialized data, so a data-dependent Makefile change (e.g. moving a Phase-2
output) can't be built there out of the box — and `make papers` also needs heavy
Quarto renders. Don't hand the load-bearing test back to the author; run the
Phase-2 slice yourself.

**How (doudou, 0208):** the primary checkout `~/CNRS/projets/actifs/climate-finance-het/`
holds the real ~440 MB contract files at repo-relative `data/catalogs/`
(no `CLIMATE_FINANCE_DATA` override → Python `DATA_DIR` = `<repo>/data`). Symlink
just the gitignored contract files into the worktree's `data/catalogs/` — leave
the committed `.dvc` files untouched:

```bash
for f in refined_works.csv refined_embeddings.npz refined_citations.csv semantic_clusters.csv; do
  ln -s "$PRIMARY/data/catalogs/$f" "data/catalogs/$f"
done
```

Then `make <target>` resolves both sides: the Makefile's repo-relative
`data/catalogs/…` prereqs AND Python's `DATA_DIR/derived/…` writes point into the
worktree, so a new `data/derived/tables/` is created fresh — exactly the wiring
under test. Build the affected Phase-2 targets directly (fast, deterministic):
producers land the moved files at the new path, consumers read them from it. This
validated all four moved files end-to-end against the 28K-paper corpus without
the Quarto render. The symlinks + generated outputs are gitignored — no pollution.

**Why:** the interesting risk in a path-eviction is the Phase-2 producer/consumer
wiring, not the PDF render. Test the slice that carries the risk. Guards: `ln -s`
into an existing non-empty dir creates a nested link (`data/catalogs/catalogs`) —
clean it with a targeted `rm` (the destructive-bash guard blocks `rm -rf`).

**How to apply:** for any worktree change that a full build would exercise but the
worktree lacks data for, symlink the primary's materialized inputs and run the
affected sub-targets rather than deferring to the author. Related:
[[feedback_stale_worktree_make]], [[feedback_make_corpus]], [[project_worktree_env_data]].
