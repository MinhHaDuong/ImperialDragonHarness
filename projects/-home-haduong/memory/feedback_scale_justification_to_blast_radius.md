---
name: branch-and-pr-is-mandatory-but-the-depth-of-justification-scales-with-blast-radius
description: "Applying the full protocol — long rationale, full test suite, cost tables — to a zero-risk doc change burns a session for six lines"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8338b22f-c41f-4090-8d0f-128df0e26867
  modified: 2026-09-15T20:42:20.168Z
---

"Everything lands via branch + PR" is a **mechanism**, cheap and non-negotiable.
The **depth of justification and verification** is a separate dial, and it scales
with blast radius. Conflating the two turns a six-line trim of a status file into
two branches, two PRs, two full test-suite runs and a table of per-line costs.

**Why:** after breaking `main` (a gate failure of my own making), the correction
went uniform instead of targeted — verification rose everywhere rather than where
the risk was. The deeper cause is that nothing in the loop compares what an
artifact is worth to what it costs to produce, so effort defaults to maximum and
only the author's irritation stops it. The micro-turn rule measures waste from
poor batching; it says nothing about matching effort to stakes.

**How to apply:**
- A docs-only change with no code path takes the docs/lint gate, not `make check`.
- Size the commit message and PR body to the blast radius. A line-count trim needs
  a sentence, not a table.
- Batch author decisions into one round. Asking "which lines?" twice is two rounds
  of the author's attention for one decision.
- Before a task whose output is small, say what it will cost and let the author
  stop it.

Cost, 2026-09-15 (search-works-for-zotero): cutting STATE.md from 60 lines to 42
consumed a large share of a session. The author's verdict: "60% de contexte pour
supprimer 6 lignes."

Related: [[feedback_memory_index_follows_start_cwd]] — the other failure of that
session, and the reason the repo's own store never reached it.
