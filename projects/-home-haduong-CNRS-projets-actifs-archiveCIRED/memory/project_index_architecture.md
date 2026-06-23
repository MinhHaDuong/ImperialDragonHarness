---
name: project-index-architecture
description: Two-layer index architecture — file_index.json (physical) and doc_index.json (logical documents)
metadata: 
  node_type: memory
  type: project
  originSessionId: be1e835b-17e0-441d-84ec-bcb75c0f8549
---

**Two-layer indexing pipeline** (complete as of 2026-05-16):

- `outputs/file_index.json` — 1991 physical files, all archive dirs. Fields: fichier, taille, hash, ext. No id field (fichier is natural key). Built by `src/build_file_index.py` (ticket 0010).

- `outputs/doc_index.json` — 1112 logical documents, full archive. 3-pass grouping: (1) hash identity → doublon, (2) canonical_key(filename) → variante/ocr, (3) post-enrichment Titre+Auteur+Année fallback → groupe_incertain. Built by `src/build_doc_index.py` (ticket 0011). Replaces `outputs/index.json` (ticket 0002).

**Why:** Coverage dropped from 741 docs (docs/ only) to 1112 (full archive) but metadata % fell (annee=57.8%, auteurs=72.8%) because attente/ and TDM/ files lack rich metadata. Cleanup deferred to future tickets.

**How to apply:** When tickets reference index.json or ask about the document index, point to doc_index.json. file_index.json is the physical-layer input.
