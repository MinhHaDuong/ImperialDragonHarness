---
name: Tech rep split into corpus + analysis
description: Technical report split into corpus-report.qmd and slimmed technical-report.qmd (2026-04-14)
type: project
originSessionId: be8aa033-fcba-4d45-933d-2863514380e8
---
The single technical report was split into two documents:

- **corpus-report.qmd** — corpus construction, enrichment, filtering, data quality (metadata/embedding/citation), core-vs-full definition, reproducibility. Includes data paper tables and figure (tab_corpus_sources, tab_languages, fig_bars).
- **technical-report.qmd** — analysis only: structural breaks, thematic structure (alluvial, clustering, temporal), polarization (bimodality, PCA), citation analysis (genealogy, cocitation). Brief corpus summary paragraph at top.

**Why:** Companion paper had three fatal problems (duplicated tech rep, two orthogonal contributions bundled, circular validation). Rather than submit it, useful content feeds back into the analysis tech rep (step 2, not yet done). The corpus part was cleanly separable.

**How to apply:** The companion paper is still in the repo but should not be submitted. Step 2 (merging companion lit review and discussion into analysis report) is pending. The periodization paper (continuous divergence, external validation) is a separate future epic.
