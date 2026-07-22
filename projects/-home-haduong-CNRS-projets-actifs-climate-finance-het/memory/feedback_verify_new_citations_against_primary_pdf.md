---
name: feedback-verify-new-citations-against-primary-pdf
description: "before adding or correcting a citation in the manuscript, grep the locally staged primary-source PDF for the exact claim — caught three real errors in one editing session"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4416da70-2381-4a58-904a-29125c1a1dde
---

During ticket 0243's citation-precision rounds (2026-07-15, PRs #1045/#1051),
checking the actual locally staged primary-source PDF (`docs/articles/*.pdf`,
via `pdftotext`) before finalizing a citation caught three real errors that
would otherwise have shipped:

1. A Bali Action Plan MRV citation pointed at para 1(e) (financial resources)
   — the "measurable, reportable and verifiable" phrase is actually in para
   1(b)(ii), which explicitly ties financing to MRV. Found by grepping the
   PDF text, not by trusting the existing citation.
2. A claim that the Paris Agreement "speaks simply of financial resources
   and mobilization" without using "climate finance" — false; the phrase
   appears 4 times in Decision 1/CP.21, 3 of them inside Article 9. Found by
   `grep -ic "climate finance"` on the PDF text.
3. A paragraph comparing a UNFCCC $340-650bn global-total estimate to the
   $100bn Copenhagen pledge as if commensurable — the report's own text
   breaks the total down by scope, and the pledge-comparable subcategory is
   ~$35-50bn, an order of magnitude smaller. Found by reading past the
   headline number to the report's own breakdown table.

**Why:** each error was the kind an editor's ear can't catch — it reads
fine, cites a real document, and only breaks under a scope/paragraph-level
check against the primary text itself.

**How to apply:** when adding a new citation or defending/correcting an
existing one in this manuscript, don't stop at "the bib entry exists and the
claim sounds plausible." Run `pdftotext docs/articles/<key>.pdf -` and grep
for the specific phrase, paragraph, or figure being cited. If the PDF isn't
staged yet, stage it (EDM workflow) before citing, not after. This is the
citation-level instance of [[feedback_manuscript_number_provenance]] (cite
only pipeline numbers traceable to an archived output) — the primary-source
analogue for numbers and claims sourced from external documents rather than
the analysis pipeline.
