---
name: feedback_manuscript_number_provenance
description: "Cite only pipeline-derived numbers that trace to an archived/reproducible output; the manuscript is v1-pinned, so live-pipeline stats can silently drift"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 64fb57ce-24c2-4d58-8219-16ebb1ea2f8f
---

Every pipeline-derived statistic in the Oeconomia manuscript must trace to a
verifiable archived output. The manuscript is pinned to v1 frozen data
(`manuscript-vars.yml`, `config/v1_*`), but the technical-report includes are
regenerated on the *current* corpus — so numbers copied from them (silhouette,
ARI, modularity, community counts, HHI series) can silently disagree with the
v1 figures the manuscript actually ships.

**Why:** the 0.68 pre-2007 modularity in §1.5 matched neither v1 (no archived
record) nor the current pipeline (0.18→0.45). The editor's whole E3 complaint
was that the quant is "transparent but unjustified" — an unreproducible number
is the worst case of that.

**How to apply:** before citing a computational number in the body, confirm it
comes from an archived artifact for the corpus version the manuscript is pinned
to. When pinned to frozen data, prefer a qualitative claim and defer exact
per-window values to the companion technical report (what A.4 now does). Treat
`clustering-comparison.md` (and any include marked "AI-generated, not
human-reviewed") as current-corpus, not v1. See [[feedback_oversell_breaks]].
