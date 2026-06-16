---
name: project_release_needs_codedata_doi
description: "Disseminating the paper is not disseminating the work — a release sequence must give code+data a persistent DOI, not just a GitHub URL."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7b53f61c-a20c-44df-a541-3fc6bab72c28
---

Before closing any dissemination/release sequence, check that the **code and
data** have a persistent, citable identifier — not only the paper. The
mission (MASTERPLAN North star) is data whose errors are *locatable*, which
requires a citable deposit; a GitHub URL is mutable and not a persistent
identifier. A paper-channel tracker (HAL, arXiv, homepage, lab announcement)
disseminates the manuscript and silently omits the artifact that the mission
is actually about.

2026-06-16: the dissemination tracker [[0663]] had no code+data DOI child.
A pre-close reflection against the mission + the author's *Research Excellence
à la Française* (REALF) caught it; deposited a Zenodo snapshot of tag
`economia-2026-report` → **concept DOI 10.5281/zenodo.20715179** (all
versions) + version DOI .20715180. Recorded in `Ha-Duong.bib`
(`Ha-Duong2026:AEDISTcode`).

**How to apply:**
- Cite the Zenodo **concept** DOI (not the version DOI) in the manuscript so
  the line survives every new snapshot; the preprint snapshot versions in
  under the same concept DOI ([[0677]] tracks the manuscript citation).
- The reconciled reference dataset gets its own citable home in the **data
  paper** [[0517]]; the Zenodo snapshot is the interim reproducibility
  artifact, complementary not redundant.
- Treat "is the code+data citable?" as a release-sequence exit criterion.
