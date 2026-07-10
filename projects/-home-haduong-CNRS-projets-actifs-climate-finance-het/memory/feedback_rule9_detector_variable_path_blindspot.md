---
name: feedback_rule9_detector_variable_path_blindspot
description: The arch-rule-9 test misses contract reads via a path variable — its detector matches read-call and contract-filename on the SAME line only
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8a8b0140-8878-4ec5-87af-1530de261357
---

`tests/test_arch_compliance.py::TestCorpusThroughLoaders` detects rule-9
violations (direct `pd.read_csv`/`np.load`/`read_feather` on `refined_works` /
`refined_citations` / `refined_embeddings`) by scanning for a **read call and a
contract filename on the same line**. So `pd.read_csv(works_path)` — where
`works_path` defaults to `os.path.join(CATALOGS_DIR, "refined_works.csv")` a few
lines up — is **invisible** to it. The literal and the read are on different
lines.

**Why it matters:** the test gives false confidence. It caught ticket 0185's
violation only because a human reviewer eyeballed it (PR #876), not because CI
did. A sweep after 0185 (2026-07-09) found the identical pattern still live in
`plot_heatmap_communities_clusters.py:270`, `plot_fig45_pca_scatter.py:357`, and
`export_citation_coverage.py:37` — all reading a `works_path`/`refined_path`
variable that defaults to the `refined_works.csv` literal.

**How to apply:** when migrating a script to the loaders, don't trust green
rule-9 CI — grep for `read_csv(<var>)` / `np.load(<var>)` where `<var>` traces to
a contract-file default. To close the blind spot for good, strengthen the
detector to flag a read whose argument is a variable assigned a contract literal
anywhere in the function (or simpler: flag any Phase-2 `pd.read_csv`/`np.load` not
routed through `pipeline_loaders`, seeding the current offenders into
`KNOWN_VIOLATIONS` and burning them down). The migration itself is byte-safe when
the only figure-relevant coerced column is `year` and a `if "." in year` label
guard already exists; the fix mirrors the `cit_path` conditional already present
in the same function (explicit `--input` path → direct read; default `None` →
loader).
