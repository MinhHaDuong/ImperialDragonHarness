<!-- last-reviewed: 2026-08-14 -->
# PDF finishing standard

Quality bar for any PDF deliverable that leaves the workshop — journal
submission, preprint deposit (HAL, Zenodo), personal page, report handoff.

**Keyword: « finition ».** This pass runs when the author asks for it, and the
agent *proposes* it when a deliverable enters finalization (submission, deposit,
upload imminent). Never during drafts: while content moves, pagination polish
is churn — the finishing pass presupposes frozen content.

## Automate first, paginate by hand never

Layout intent belongs in the header/config, declared once — not in
hand-inserted `\newpage` rounds that any upstream edit re-opens (cost of
skipping: 8 interactive re-render rounds on the Œconomia page-perso variant,
2026-07-22). For a Quarto/LaTeX build, the standard knobs:

- **Sections on fresh pages** (long-form ≥ 20 pp):
  `\usepackage{titlesec}` + `\newcommand{\sectionbreak}{\clearpage}`.
- **Widows and orphans**: `\widowpenalty=10000 \clubpenalty=10000`.
- **Pipe-table column widths**: pandoc maps the delimiter-row dash counts to
  relative widths — set the ratios there; narrow the label columns, give the
  analytic columns the room. Only if a longtable still splits, one `\newpage`
  before it.
- **Bibliography density**:
  `\AtBeginEnvironment{CSLReferences}{\small\setlength{\parskip}{0.3em}}`.

## The finishing checklist — verified by script, not by eyeballing

Run a `pdftotext` sweep over the rendered PDF and check mechanically:

1. No table or figure split across pages; caption on the same page as its float.
2. No heading as the last line of a page; no 1–2-line widow above a heading
   at a page top.
3. No missing glyphs (grep the extraction for `�` / check `pdffonts`) —
   math-mode symbols, not text-mode Unicode, for ≈/≤/… in Latin Modern.
4. Page size intentional (A4 unless the venue says otherwise), page count and
   metadata (title, author) match the variant.
5. Identity matches the variant: anonymous builds carry zero de-anonymizing
   strings (grep author name, repo URLs, DOIs); named builds carry the
   restored links.
6. Links resolve: spot-check DOIs and URLs added at finishing time.

Eyeballing the PDF stays mandatory for what scripts can't see
(`feedback_visual_verify_citations`), but the pagination sweep is script work.

## Variants are transform layers

A named/deposit variant (HAL, page perso) is a script that applies string
transforms to the shared source, renders, and reverts (`apply → render →
git checkout --`). The script is archived beside the release artifacts, so
the variant is reproducible. Reference implementation:
`papiers/sent/Oeconomia_Inventing_Climate_Finance/releases/hal_variant.py`
(climate-finance-het, 2026-07-22).
