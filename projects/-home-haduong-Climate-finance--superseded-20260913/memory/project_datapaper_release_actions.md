---
name: project_datapaper_release_actions
description: Data-paper release checklist — Zenodo retitle and version-string sync that only the author can do at the new-version upload
metadata: 
  node_type: memory
  type: project
  originSessionId: e1a2a449-f55d-4143-847e-e015213fee2a
  modified: 2026-07-27T18:38:56.134Z
---

Three things are deliberately left undone in the repo until the data paper's
Zenodo deposit is re-uploaded. They are not defects; they are release-time
actions no agent can perform, because they touch a published record.

The runbook is `deliverables/data-paper/revision-rdj26561/ed04-zenodo-restructure-upload.md`
(record 19236130 → **New version**). At that upload:

1. **Retitle the record.** As of 2026-07-27 the live record (v1.1, published
   2026-03-26) still reads *"A Curated Corpus of Climate Finance Literature,
   1990–2024: Six Sources, Multilingual Retrieval, and Grey Literature"*. The
   new title, matching the paper and already written into the runbook, the
   related-dataset entry, the suggested citation and the archive README, is:

   > A Curated Multi-Source Corpus of Climate Finance Literature, 1990–2024:
   > Multilingual Retrieval and Grey Literature

   The count left the title on purpose (author, 2026-07-27) — a number pinned
   there goes stale at every harvest, which is how "six" survived into v2. The
   source count lives in the prose as `{{< meta corpus_sources >}}`.
   `TestSourceCardinality` in `tests/test_datapaper_archive_layout.py` now
   rejects any spelled-out count in the paper or the archive README.

2. **Sync the version string in the paper.** `data-paper.qmd` §"Zenodo deposit"
   still describes `data/products/` as holding "the v1.1 corpus files". The
   runbook suggests publishing as v2.0. Whatever version is actually set at
   upload has to be written back into that sentence — it is hand-typed, not
   macro-driven, and nothing guards it.

3. **Keep the concept DOI, not the version DOI.** Use Zenodo's *New version*
   button so the version chain is preserved; adding the record manually
   duplicates the chain (already noted in the runbook).

Scope note: the Œconomia manuscript and the Gide slides correctly say "six
sources" — `manuscript-vars.yml` is pinned to the v1.0 corpus. Do not sweep
them. See [[feedback_union_only_defects]] for why the guard is scoped.
