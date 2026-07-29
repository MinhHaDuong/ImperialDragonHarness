---
name: project-rdj26561-rr-round1
description: "RDJ-26561 data paper R&R round 1 COMPLETE — revision 1 resubmitted 2026-07-29, awaiting editor; upload-kit recipe for round 2"
metadata: 
  node_type: memory
  type: project
  originSessionId: 03c497a7-5c6e-462e-b38e-55b54e94f44a
  modified: 2026-07-29T16:28:58.841Z
---

RDJ4HSS data paper (RDJ-26561): revise-and-resubmit received 2026-07-20
(coeditor Cédric Chambru, one referee); **revision 1 resubmitted 2026-07-29**
via the journal platform (author upload), well ahead of the ~2026-10-20
deadline. Tracker 0274 and release ticket 0283 closed; paper track moved to
`papiers/sent/RDJ4HSS_Curated_Corpus_Climate_Finance/`. Editor acknowledged
reception 2026-07-29 and said he would look at it before his summer leave
the following week — decision window possibly early August 2026.

Frozen state: tag `rdj26561-revision1` (= submission/rdj-data-paper branch),
Zenodo v2.0.0 (version DOI 10.5281/zenodo.21679237, concept .19236129 —
concept resolves to latest but lags right after a deposit), HAL
hal-05570600v2. Corpus v2: 8 sources, 43,179 unified → 33,344 refined.

Upload kit (reuse the recipe at acceptance / round 2), archived in
`papiers/sent/.../release/2026-07-29-RDJHSS-revision1/`:
- Journal wants: Word file, 2-8 lowercase keywords below abstract, figures
  AND tables as separate numbered files, acknowledgements as separate file,
  APA 7. Guidelines PDF: researchdatajournal.org/libraryFiles/downloadPublic/211.
- `DataPaper.docx`/`.pdf` render from `deliverables/data-paper/data-paper.qmd`
  (`quarto render --to docx|pdf`); the two raw-LaTeX tables (sources,
  variables) carry pipe-table twins behind `content-visible` divs so DOCX
  keeps them — the variables twin is emitted by `render_markdown_table()`
  in `scripts/_deposit_variables.py`.
- Table1-5.md extract from the qmd pipe twin + the self-contained
  `deliverables/_shared/tables/tab_{corpus_flow,corpus_sources,languages}.md`
  + the variables pipe twin; Figure1.png = `fig_global_map_direct.png`.
- Homepage: paper entry (`@techreport`, file→local PDF, HAL eprint, doi slot
  reserved for the future journal DOI) + separate dataset entry (`@misc`,
  concept DOI), linked via `relations` — AEDIST pattern.

Word budget note: v1 was trimmed to 2,495 words; the machine cut to 2,497
(PR #1115) was rejected by the author, and revision 1 shipped at ~3,700+
prose words with the editor-requested additions — the author's deliberate
call, not an oversight.
