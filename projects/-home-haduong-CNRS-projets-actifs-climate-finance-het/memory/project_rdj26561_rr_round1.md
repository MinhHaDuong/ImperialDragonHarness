---
name: project-rdj26561-rr-round1
description: "RDJ-26561 data paper R&R round 1 — tracker 0274, deadline ~2026-10-20 (soft, verified); 0288 BUILD merged, 0304 harvest is the critical path"
metadata: 
  node_type: memory
  type: project
  originSessionId: 03c497a7-5c6e-462e-b38e-55b54e94f44a
  modified: 2026-07-22T18:23:47.238Z
---

RDJ4HSS data paper (RDJ-26561) got a revise-and-resubmit 2026-07-20 (coeditor
Cédric Chambru, one referee). Deadline ~2026-10-20 — soft, verified on the
archived letter ("within three months", received 2026-07-20).

- Tracker: ticket 0274; remark ledger
  `deliverables/data-paper/revision-rdj26561/ledger.dedup.jsonl` (15 remarks).
- **0288 BUILD phase merged 2026-07-22** (PR #1085, after review with 2
  verified fixes + author decisions on keywords/stems): corpus-v2 curated
  key-documents layer (unfccc + oecd sources, symbol identifiers, no DOIs,
  abstract_provenance + keywords_provenance disclosure columns, curated-source
  protection channel). Starter seeds 47 UNFCCC + 14 OECD in
  `config/{unfccc,oecd_dac}_sources.yaml`.
- **Critical path is now 0304** (renumbered from 0293 — seat taken): complete
  the seed enumeration (UNFCCC ~150–300 via a facet-crawl discovery script on
  unfccc.int/documents — Topic="Climate finance" facets verified; OECD via
  manual OLIS export, One returns 403), full `--fetch` harvest **on padme**
  (coordinate with author), Phase-1 rerun, probe regression (classes A/B must
  match). Blocks final corpus numbers; prose drafts on v1 numbers, final
  render waits.
- Sibling wave merged 2026-07-22: 0284 (dedup run report), 0285, 0289
  (prior-mappings overlap), 0263 triage. Heavy ticket renumbering that day —
  fetch before allocating IDs.
- Still open: 0275/0278/0281 prose (sequence, same file), 0279 variables
  table (must cover the 4 new columns — note propagated, PR #1089), 0280
  Zenodo (waits on deferred 0287 CSV decision to avoid double version bump),
  0286 figure (needs-human), 0283 response letter last (1st person singular).
- Corpus probe: 310 OECD 10.1787 works already in via OpenAlex — only
  pre/non-DOI founding documents harvested; DOI polarity is the dedup
  boundary (seeds must NOT carry DOIs).
- Sources archived at
  `~/CNRS/papiers/actif/RDJ4HSS_Curated_Corpus_Climate_Finance/2026-07-20 decision/`
  (moved from papiers/sent/).
