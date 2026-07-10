---
name: reference_bib_fulltext_index
description: How docs/articles fulltext links to main.bib via file= fields; OA-fetch and DOI-title audit method
metadata: 
  node_type: memory
  type: reference
  originSessionId: 796836f2-caf1-4c02-8aa0-ad83e8baacbd
---

`content/bibliography/main.bib` is the citation DB for all `content/*.qmd`
(via `bibliography: bibliography/main.bib`). Local fulltext PDFs live in
`docs/articles/` (gitignored → Zotero at publication, see
[[reference_cited_works_local_docs_articles]]).

**Indexing convention (built #893/#899, 2026-07-08):** each entry with a local
PDF carries `file = {docs/articles/<bibkey>.pdf}`; the PDF is named exactly
`<bibkey>.pdf`. Quarto ignores `file=`; it serves the reference manager. After
#899, 147/181 entries are linked. The ~34 unlinked are genuinely paywalled
(copyrighted books, closed Elsevier/JSTOR) — no legit OA. Two tiny landing-page
stubs sit in `docs/articles/_superseded/`.

**Fetching OA fulltext:** deterministic Unpaywall→curl first
(`api.unpaywall.org/v2/<doi>?email=...`, validate magic bytes + `pdfinfo`),
then an agent swarm on the residual (arXiv/HAL/Semantic Scholar/Europe PMC/
author pages). Legit OA only — never Sci-Hub/LibGen. Always re-validate on disk
(magic + pages + first-page title match); do NOT trust agent "fetched" flags.

**Bib integrity risk:** the bib contains LLM-fabricated entries (real title,
wrong author/DOI). The audit is now a committed tool — `scripts/qa_bib_doi.py`
(Crossref title + first-author check, subtitle/LaTeX/corporate-author tolerant)
guarded by `tests/test_bib_doi_title.py` (fast unit + one @slow live audit, PR
#908 / ticket 0164). It fixed 6 more entries 2026-07-08: author lists on
`puccetti2021`→Kozlowski, `poetto2023`→Taher Harikandeh, `lealarcas2021`→Zamarioli,
`simonet2022`→Simoens; DOIs on `dahan2010` (shpsc→shpsb) and `blei2003` (dead
JMLR DOI→url). Earlier #899 pass fixed `delvenne2017`/`li2021`. The last three
(`manne_richels1992`, `atwoli_etal2022`, `min2021measuring`) closed 2026-07-09
via ticket 0188 / PR #928 after author calls: manne → `@book` MIT Press 1992 (no
DOI); atwoli → BMJ `10.1136/bmj.n1734` (the `bmj.n2177` you find on the web is a
*news item about* the editorial, not the editorial); min → the titled paper did
not exist (fabricated title+DOI), replaced with the real Min/Bu/Sun 2021 techfore
paper `10.1016/j.techfore.2020.120502`. `KNOWN_WRONG_PAPER` is now empty — the
@slow gate runs unallowlisted, so a new suspect fails CI. Subtitle-truncation,
LaTeX accents, and arXiv/figshare DOIs (10.48550, 10.6084) are non-defects.
