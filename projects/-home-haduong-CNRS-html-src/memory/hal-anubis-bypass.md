---
name: hal-anubis-bypass
description: How to fetch HAL deposits when the hal.science web frontend is Anubis-walled
metadata: 
  node_type: memory
  type: reference
  originSessionId: c2eb4049-9136-4d7d-994f-33814cd6ac75
---

When the `hal.science` web frontend is behind the Anubis anti-bot wall (WebFetch
returns "Access Denied"), two HAL endpoints bypass it:

- **Structured search**: `https://api.archives-ouvertes.fr/search/?q=...&wt=csv`
  — full Solr query API. Useful fields: `halId_s, title_s, language_s, docType_s,
  files_s, fileMain_s, producedDate_s`. `files_s` lists *every* file in a deposit
  (a bilingual VIETSE report often bundles EN + VN PDFs under one halId with a
  bilingual `title_s`). Filter by author: `authFullName_t:"Minh Ha-Duong"`.
- **File download**: the per-deposit subdomain endpoint
  (`enpc.hal.science/<halId>/file/<name>.pdf`, `shs.hal.science/...`) serves the
  raw PDF with plain `curl` — not Anubis-walled.

Used in ticket 0016 to recover the Vietnamese biomass policy note bundled inside
hal-03059625. The author's local `~/CNRS/papiers/published/` tree is the other
recovery channel for dead-site (vietse.vn) VN PDFs.
