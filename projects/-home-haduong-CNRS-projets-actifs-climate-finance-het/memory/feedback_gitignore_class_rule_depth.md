---
name: feedback_gitignore_class_rule_depth
description: "a class rule over .gitignore files must be one level deep, and a .gitignore holding `*` or a negation is load-bearing by construction"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 78accd55-356d-44d9-b79e-e6471e94c518
  modified: 2026-09-10T09:08:43.793Z
---

Quarto rewrites a two-line `.gitignore` (`/.quarto/` + `**/*.quarto_ipynb`) into
every project directory it renders, so those files come back after every
deletion. The durable fix is a class rule in the root `.gitignore` —
`deliverables/*/.gitignore`, **one level, never `**`**.

**Why:** the two-level variant (`deliverables/**/.gitignore`, or any
`find <dir> -name .gitignore` sweep) also swallows
`deliverables/slides-gide/slides-assets/.gitignore`, which sits one segment
deeper and keeps three copyrighted images out of this **public** repo. Untracking
it is silent, exits 0, and the bill arrives on a fresh clone when someone renders
the slides. Landed 2026-09-10 as PR #1314.

The sweep that followed found the sharper discriminator, better than depth:
**a `.gitignore` containing `*` or a `!` negation is load-bearing by
construction** — `data/het/`, `tests/fixtures/smoke/` and
`tests/fixtures/smoke/catalogs/` each use `*` plus a whitelist, and three of them
negate themselves (`!.gitignore`). Untracking any of those would collapse the
whole directory's tracking policy, a far worse outcome than the slides case.
None sit under `deliverables/`, so no live defect — reported, not ticketed, per
the tooling-lane severity floor.

**How to apply:** before any class-wide `.gitignore` sweep, read each candidate's
content and check for `*` or `!` before checking its path depth. Prove the spared
file is genuinely spared with [[feedback_check_ignore_needs_no_index]] — a bare
`check-ignore` on a tracked file cannot answer.

Side effect accepted and documented in the file itself: a future legitimate
`.gitignore` at a deliverable's first level now needs `git add -f`.
