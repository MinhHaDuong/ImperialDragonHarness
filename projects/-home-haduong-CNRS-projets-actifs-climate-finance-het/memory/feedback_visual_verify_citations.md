---
name: feedback_visual_verify_citations
description: Render the PDF and eyeball it — visual verification catches citation/bib errors that grep and CI cannot
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a71c13b1-4a51-47a5-a757-8a3af332cb10
---

Always render the manuscript PDF and visually inspect it before calling a paper done. The Gide wrap-up found errors that grep and CI could not: `corfee-morlot2009` cited the wrong *paper* (a cities paper, not the MRV framework), `carty_lecomte2018` had wrong author first-names, and `buchner2011/2013` rendered "Büchner" (umlaut) for Barbara Buchner. All three *resolved* fine (valid keys, valid DOIs) — only reading the rendered author-year and bibliography surfaced them. Also caught visually: a draft "15 GW" that was ~9× the real 1.7 GW, and `lang: fr` not localising crossref prefixes ("Table" vs "Tableau").

**Why:** citation correctness is semantic, not lexical. A key that exists and a DOI that resolves can still point to the wrong work or carry a wrong name — invisible to grep and to a DOI-resolution test.

**How to apply:** after `make gide` (or `quarto render`), read the rendered pages (Read tool renders PDF pages as images) — front matter, every figure/table caption, the bibliography. Treat the visual pass as a required gate, not a nicety. Systematic bib validation is tracked in ticket 0164. See [[feedback_manuscript_number_provenance]].
