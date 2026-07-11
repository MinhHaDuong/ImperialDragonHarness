---
name: reference-openalex-pre1970-citations
description: "OpenAlex can't do reference-based (outgoing) citation analysis for pre-1970 works; incoming citations are reliable, outgoing/2-hop is a structural null."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3d931939-f824-43ba-bbb6-6993ee0dedae
---

2026-07-08, established by a 90k-token agent run for the HET Figure 1 (`conception/het-indirect-citations.md`, PR #23):

**OpenAlex does not index the outgoing reference lists of pre-1970 works.** A direct-citation crawl among the 15 HET primaries (1916–1984) recovered only 1 of 5 known edges; the 2-hop indirect analysis `A ∩ cited-by(cited-by(A))` was a **structural null** — not evidence of no connection, just missing data. Two reasons: (a) old works have no indexed `referenced_works`; (b) many resolve only to modern reprints (de Finetti 1937 → a 1992 Springer record), so a year-bounded query excludes them.

**What works vs not, for old works:**
- **Incoming** citations (`filter=cites:ID`, who-cites-X) ARE reliable — modern citers are indexed. Any analysis must be built from incoming queries only.
- **Outgoing** references / bibliographic coupling / anything needing the old work's own reference list — infeasible.
- Some pre-1960 works don't resolve at all (Heckscher 1916 Swedish; Samuelson 1952 AER absent / title-search false positives).
- Free tier now caps at **1000 requests/day** (`retry-after` ≈ 11h).

**How to apply:** for any citation-structure figure/analysis over mid-century sources, don't promise a reference-overlap or indirect-bridge result from OpenAlex — it can't. The trustworthy route is hand-transcribing the bibliographies (as the HET direct citations were, into `tab:citations` / `citations_verified.csv`). State shared-reference claims qualitatively from the hand-audit, not from a database crawl. Related: [[feedback-verify-uncommitted-files-before-acting]].
