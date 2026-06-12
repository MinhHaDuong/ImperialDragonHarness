---
name: project-exp1-design-decisions
description: Experiment 1 baseline design decisions locked in session 2026-05-15
metadata: 
  node_type: memory
  type: project
  originSessionId: deab15ae-916a-4088-89c1-cfb8a32815c8
---

**Prompt:** modules 2_goal + 5_table (no persona, no overview, no quality guards).

**URL sourcing is intentionally unguarded:** `5_table.txt` asks for URLs (`- Sources: specify where in the document, include URL`) without module C_Uncertainty's anti-fabrication guardrail. Design intent: test baseline hallucination. URL fabrication rate is an observable (unscored) signal in the no-RAG condition.

**>30MW filter** appears in both 2_goal ("past, present and future thermal generation assets >30MW") and 5_table (`Total MWe: Include units > 30MWe`). Table spec is self-contained.

**Notes column** added to table — lets models express uncertainty inline rather than dropping rows.

**Pending before sweep (ticket 0175):**
- Update harness.py _MODULE_ORDER for new module names
- Update modules/README.md assembly order
- Update experiments.toml sweep_ablation_p1_direct_base to reference 2_goal + 5_table
- Update Annex A in slides/manuscript/main.md (still shows old base.txt content)

**Why:** Locked 2026-05-15. Ticket chain 0174–0178. Branch t0174-exp1-baseline pending review.

**How to apply:** Ticket 0175 must close before ticket 0177 (sweep) runs. Annex A update is part of 0175 exit criteria.
