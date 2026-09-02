---
name: atomic-prs-short-branches
description: "The author favours short-lived branches and atomic changes - one concern per PR, never fold a small deliverable into a passing larger one"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9970023e-fc7f-4ab4-80ee-07075e1dc25f
  modified: 2026-09-01T06:01:36.452Z
---

Author directive, 2026-09-01, verbatim: "Not folded here. I favour short
lived branches and atomic changes." Said when a small upstream disclosure
was proposed to ride the next larger filing; he wanted it standalone. The
same session landed five one-concern PRs in a row (a ruling, a norm, a
ticket filing, a SYNC row) each on its own branch, merged within minutes.

**Why:** atomic changes keep the review surface honest and the history
legible; a folded extra is invisible in the title and survives review by
association.

**How to apply:** when a session accumulates several small deliverables,
land each on its own short-lived branch with its own PR, sequentially —
don't batch them into one commit or ride them on an unrelated PR. This
extends the one-change-per-commit rule up to the PR level, and it applies
to upstream filings too (the courtesy-filing norm's "standalone, never
folded" clause is this preference, ratified).
