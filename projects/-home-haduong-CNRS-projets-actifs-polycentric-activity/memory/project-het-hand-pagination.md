---
name: project-het-hand-pagination
description: "HET manuscript §3 is hand-paginated (one \\newpage per discovery, widow penalties 10000) — any added BODY line spills a page, but a footnote costs nothing; batch the pagination arbitrage after all PRs land"
metadata: 
  node_type: memory
  type: project
  originSessionId: a4553684-97f9-418a-ba2a-4f61c23b7dd5
  modified: 2026-08-17T15:32:59.917Z
---

The HET manuscript (`article-het/manuscrit.tex`) hand-paginates §3: one
`\newpage` per discovery subsection, each tuned to fill its page, with
`\widowpenalty=\clubpenalty=10000`. Consequence observed on PRs #88 and #89
(2026-08-13): ANY line added to the *body* of a full subsection spills a block
onto a fresh page (3-line spills, 36→38 pp.), and no agent may cut author prose
to buy the page back.

**The rule is about the body, not the apparatus.** Measured 2026-08-17 (PR #145,
Beckmann added to §3.1): an eight-line `\footnote` on the last paragraph of §3.1
cost **zero pages** — 39 before, 39 after, §3.1's body still ending at the foot
of p. 11 and §3.2 still opening p. 12. A footnote draws on the bottom-of-page
reserve, which body prose cannot use. So « tout ajout déborde » is true of body
text and false of notes, and that distinction decides what can be added to §3
without repaginating. Cheap material for §3 is therefore a footnote, not a
sentence.

**Why:** a body spill is structural, not a defect — flagging it as REROLL wastes
review rounds; cutting prose to fix it oversteps author arbitration. And
assuming the spill without building wastes the cheaper option: the build is
seconds (`cd article-het && make`, tectonic), so measure rather than predict.

**How to apply:** build before and after and report the page count, never the
prediction. Agents adding *body* text to §3 report the spill with options and
leave pagination to the author; when several manuscript PRs are in flight,
propose ONE pagination arbitrage after the last one merges (the author did
exactly this for #88+#89). Final repagination belongs to the « finition »
pass (rules/pdf-finishing.md), once content freezes.
