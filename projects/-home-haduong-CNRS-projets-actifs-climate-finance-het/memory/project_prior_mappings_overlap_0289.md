---
name: project-prior-mappings-overlap-0289
description: "Empirical overlap of refined corpus vs prior climate-finance bibliometric mappings — 89-91% coverage, >99% discovery; artifacts archived under revision-rdj26561"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3008bcee-9017-4c86-952e-ac2530888aef
  modified: 2026-07-22T16:38:36.478Z
---

Ticket 0289 (PR #1083, merged 2026-07-22) replicated the published search
queries of four prior climate finance bibliometric mappings against OpenAlex
and matched them into `refined_works.csv` (normalized DOI, year-constrained
title fallback):

- Carè & Weber 2023: 89.3% (758/849) · Shang & Jin 2023: 91.0% (975/1,072) ·
  Rusydiana 2023: 91.1% (1,152/1,264) · Reis Maria et al. 2023: 40.1%
  (1,618/4,034 — their object is green finance at large, boundary not defect).
- **Decomposition is the argument**: discovery coverage (pre-filter) is >99%
  for the three climate finance populations; the 89–91% headline is our own
  curation (flags `citation_isolated_old`/`no_abstract_irrelevant`, median
  1 citation, none ≥50). Of 11 never-captured works, 7 entered OpenAlex
  *after* our 2026-03-22 harvest (repository backfills) — snapshot corpora
  decay retroactively even for their own period.
- Artifacts: `deliverables/data-paper/revision-rdj26561/`
  (`probe_prior_mappings_overlap.py`, `prior-mappings-overlap.{md,csv}`,
  `prior-mappings-misses.csv`). Probe is manual-run (phase separation),
  needs the OpenAlex premium key.
- Prose staged for the R&R added-value reply (tickets 0278/0283, tracker
  [[project-rdj26561-rr-round1]]): `deliverables/_shared/_includes/prior-mappings.md`
  (part A, author-reviewed, marker cleared) + a response-letter bullet inside
  `prior-mappings-overlap.md`. Part B (`bibliometric-context.md`, clustering
  validity) stays orphaned pending ticket 0290.
- Process fixes ticketed as 0298 (harvest cadence + `from_updated_date`
  pass + discovery-recall ≥95% gate against these external queries); the
  language-null-rate regression (4.1%) is ticket 0297. Both renumbered from
  0295/0296 after a seat collision with parallel merges — first-merged wins,
  latecomer renumbers.
