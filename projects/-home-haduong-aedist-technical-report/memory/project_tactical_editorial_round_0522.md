---
name: project-tactical-editorial-round-0522
description: "Next action after the 0509-0518 raid — execute ticket 0522 (tactical editorial pass) with best Fable, anchor-first"
metadata: 
  node_type: memory
  type: project
  originSessionId: 96516ff3-e9dd-43d9-94cc-9744a7da7120
---

The 0509–0518 arXiv-preprint raid is COMPLETE (all merged; manuscript reconciled
to 177 plants, RW split, §3 halved, symbolic cross-references via pandoc-crossref).
Follow-ups tracked: 0519 (IDH writing rule), 0520 (Exp2 new-model extension),
0521 (heatmap plot §2 literal).

**Next action: execute ticket 0522** — the tactical editorial pass on
`slides/manuscript/main.md`. It is a fully-specified handoff (intent + author
voice + review protocol). Key points:
- **Run with best Fable** (`model: "fable"`). This was blocked in the prior
  session because `advisorModel` had cached `opus`; the file now sets
  `advisorModel: fable`, so a fresh session unblocks Fable sub-agents.
- **Spine = "the constraint is data, not model"** — the author's own framing
  (2026 Econom'IA "Beyond RAG" deck: "Models need reliable data" → ASEAN
  power-system models need inventories → can AI supply them?). Funding-relevant.
- **Author voice** calibrated in the ticket from real sources: the 2026 deck
  (finding-first slide titles) + the 2024 "Vietnam at the dawn" abstract (formal
  register). Finding-first topic sentences; quantified; "however"-pivot;
  transferable so-what; de-jargon for CIRED economists; no first person.
- **Review protocol (author-chosen):** rewrite THREE anchor paragraphs (abstract
  + one finding + one figure-framing) → author proofs the tone → THEN one
  whole-manuscript PR. Do not edit the whole document before the anchor is blessed.
- Invariants: every number identical (framing only), no restructuring, symbolic
  refs intact, `make check` green (use `PYTEST_ADDOPTS=""`).

See [[project_preprint_target_main_md]], [[feedback_concurrent_pipelines_shared_tickets]].
