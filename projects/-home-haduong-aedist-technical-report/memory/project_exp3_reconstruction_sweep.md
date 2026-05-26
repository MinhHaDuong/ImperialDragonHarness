---
name: project-exp3-reconstruction-sweep
description: Exp 3 is the reconstruction-from-verified-bibliography sweep (5 strategies × 5 models × 3 reps); full spec in ticket 0202
metadata: 
  node_type: memory
  type: project
  originSessionId: a6cf5897-03f3-4beb-9433-92770830fc8e
---

Exp 3 design locked 2026-05-21 in ticket 0202.

- **Starting state**: cheapest Exp 2 Phase B deep-research output. Keep sectoral overview + bibliography; throw away inventory + table.
- **HITL three-tier verification**: Tier 1 (gov/agency/state-outlet publisher) → auto-OK + primary; Tier 2 (source in user's Zotero) → auto-OK + non-primary; Tier 3 (anything else) → present to user. Output: `experiments/exp3/verified_bibliography.csv`.
- **5 reconstruction strategies**: null (= Exp 2's unverified table), batch RAG, incremental {chronological, random, mistral-embed-ranked}.
- **State for incremental strategies** = working report (table + bibliography + per-cell provenance), structured object. Model receives (state, next doc), produces (updated state). Not a growing raw-context window.
- **Matrix**: 5 models × 5 strategies × 3 reps = 75 cells. Cost reported, not controlled.
- **Ranker**: `mistral-embed` + cosine similarity. Mistral has no dedicated cross-encoder reranker as of cutoff Jan 2026.
- **Two outputs**: `fig_reconstruction_strategies.pdf` (cost × F1 Pareto, family-coloured, whiskers) and `tab_reconstruction_quality_dims.{tex|md}` (four-dim H1–H4 table). Lands in manuscript §3.

**Why:** The original "regimes ladder" was misspecified — multi-turn is an interaction pattern, not an information regime. User respecified through a long design dialogue covering ladder shape, starting state, verification protocol, ranker choice, reps, quality readout, and figure naming. The locked design needs to survive future sessions that might otherwise re-derive it from the manuscript prose or the retired `fig_regimes_scatter` artefact.

**How to apply:** Read ticket 0202 for full spec before doing any Exp 3 work. Don't re-litigate the strategy list, the HITL protocol, the ranker choice, or reps count — all resolved. Blocker is 0166 (Exp 2 Phase B completion). Architecturally convergent with [[project-talk-narrative-three-plus-case-study]] case study (0200) — both share state object, verified bibliography, and starting state, but stay as separate tickets. See also [[project-exp1-done]], [[project-h1-h4-hypotheses]].
