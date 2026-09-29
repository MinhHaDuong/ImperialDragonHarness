---
name: feedback_author_is_not_the_checker
description: "Never route low-confidence machine judgments to the author for checking; cross-check with other models, take a stance, record confidence, serve results sorted by confidence"
metadata:
  node_type: memory
  type: feedback
  originSessionId: eae976b8-5082-4ce8-97e1-6c05a93a8951
  modified: 2026-09-29T16:15:34.285Z
---

Automated judgments (LLM adjudication, matching, dating a row from its page) are cross-checked by independent models from other vendors, blind to each other, with a positive control first. Take a stance on every row by a versioned rule (majority, confidence from agreement and self-scores), apply it as a defeasible decision with `decided_by` naming the panel, and record per row each reader's verdict and the confidence. The observatory serves the decisions sorted by confidence, so the author reviews when he wants. Only questions that change what a term or the contract means go to the author, and even then with the panel's stance.

**Why:** 2026-09-29, PR #1574: an agent's self-set 0.8 threshold routed 47 rows to the author as "items for Minh's decision". The author: "So you want to use me as a reverse centaur? How about checking automatically? ... take a stance, keep track of the confidence level, and let me examine the results sorted by confidence level when I feel like it. That's what the MVP is for." The panel (Fable, gpt-6-sol, mistral-medium) agreed 3/3 on 49 rows, 2/3 on 45, and overturned the first reader on 44. A self-scored confidence is not calibrated; the storage contract's held-out test still applies before a tier runs unattended on matching.

**How to apply:** `codex exec` and `vibe -p` are installed on doudou, but check which model each runs: on 2026-09-29 they were gpt-6-sol and mistral-medium-3.5, not the Opus and GLM the author expected. Use them also as independent code reviewers of a PR diff. See [[feedback_skeptical_advisor_before_new_guard]].
