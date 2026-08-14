---
name: project-het-hand-pagination
description: "HET manuscript §3 is hand-paginated (one \\newpage per discovery, widow penalties 10000) — any added line spills a page; batch the pagination arbitrage after all PRs land"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4553684-97f9-418a-ba2a-4f61c23b7dd5
  modified: 2026-08-13T20:15:52.923Z
---

The HET manuscript (`article-het/manuscrit.tex`) hand-paginates §3: one
`\newpage` per discovery subsection, each tuned to fill its page, with
`\widowpenalty=\clubpenalty=10000`. Consequence observed on PRs #88 and #89
(2026-08-13): ANY line added to a full subsection spills a block onto a
fresh page (3-line spills, 36→38 pp.), and no agent may cut author prose to
buy the page back.

**Why:** the spill is structural, not a defect — flagging it as REROLL wastes
review rounds; cutting prose to fix it oversteps author arbitration.

**How to apply:** agents adding text to §3 report the spill with options and
leave pagination to the author; when several manuscript PRs are in flight,
propose ONE pagination arbitrage after the last one merges (the author did
exactly this for #88+#89). Final repagination belongs to the « finition »
pass (rules/pdf-finishing.md), once content freezes.
