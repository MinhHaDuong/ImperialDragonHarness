---
name: feedback-ticket-premises-are-hypotheses
description: Agent-authored ticket premises can be confidently wrong — verify against data/code before executing a raid
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1ef5880f-4773-4ca8-a00f-f74fe0b97360
---

Ticket bodies written by earlier agents/sessions state premises with confidence that are often factually wrong. The raid Imagine/Plan phase exists to catch this — treat the ticket's diagnosis as a hypothesis and verify it against the actual data and code before launching execute agents.

**Why:** In the 0483/0486/0487/0488 raid (2026-06-09), the Imagine/Plan verification overturned **3 of 4** ticket premises:
- 0488 claimed `exp1_cross_eval.csv` had "only accuracy columns" → the coherence columns already existed (commit 5cfe68e7, ticket 0453). Ticket voided.
- 0487 claimed the Haiku heatmap false-pass was a missing-column scoring gap → the real cause was an inverted-polarity `coherence_run_veto` in the heatmap render (`cell_is_red` tests `==0`, veto `1`=bad). Re-scoped.
- 0486 named Wikipedia + OSM as coverage sources → Wikipedia is protocol-banned (§3.4) and OSM-via-Overpass is non-reproducible. Deferred for author decision.
Only 0483 (figure renumber) survived as written.

**How to apply:** Before executing a raid ticket, run the cheap data check (read the CSV header, grep the code, render the figure). If the premise fails, void/re-scope/defer with a documented non-finding rather than executing a wrong plan. Echoes the project rule "Derive prose from generated artifacts, never from agent enumeration" — extended to ticket premises. See [[feedback-autonomous-raid-doudou-pickup]].
