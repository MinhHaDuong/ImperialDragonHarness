---
name: reference-inari-archive-mapping
description: How the local doudou archive maps to inari buckets; two distinct recueil sources
metadata: 
  node_type: memory
  type: reference
  originSessionId: 61ed0557-1ef4-4ae4-bbbf-26a9da16b8d2
---

The local archive `/home/haduong/data/datasets/ours/Archives CIRED numerisées/`
is a **mirror of inari** bucket `kCj0pHP0-CIRED_numerisation` under `zotero/www/`.
Mapping: local `<relpath>` → `https://inari.centre-cired.fr/kCj0pHP0-CIRED_numerisation/zotero/www/<urlquote(relpath)>`.
Verified on both `docs/…` and `attente/à dédoublonner…/…` (HTTP 200, byte-identical sizes).

**Two distinct "recueil" sources — do not conflate:**
- `Wehurei6-recueil_50ans_CIRED` — Antonin's curated recueil-50-ans scans; the
  files behind the **131-notice Zotero group** `Recueil_CIRED_tout_importé`.
- `kCj0pHP0-CIRED_numerisation/zotero/www/` — the general CIRED numerisation
  mirror (the whole local archive, including `docs/` and `attente/`).

Cost of conflating (2026-06-24): I probed only the `Wehurei6` recueil bucket for
the 13 stub files (ticket 0018) and wrongly concluded "not on inari, single copy
on doudou." They were on inari all along, in the numerisation bucket. Diagnosis
lesson: a file absent from one bucket is not absent from inari — check the
numerisation mirror before claiming a preservation gap. See [[project_index_architecture]].
