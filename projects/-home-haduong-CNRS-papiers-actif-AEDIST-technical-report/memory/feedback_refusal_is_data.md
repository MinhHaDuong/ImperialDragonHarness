---
name: feedback-refusal-is-data
description: "When a model declines a task on principled grounds, classify and report as refusal — not as noise to be eliminated"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f4537f72-6ba0-4e22-b885-a15b15f10ed9
---

When a frontier model declines a task with refusal-opener prose ("I cannot fulfill", "I can't honestly produce", "⚠️ Critical Limitation Notice", etc.), the user's framing is: that's data, not pathology. The model is expressing a viewpoint on the request's epistemic standard.

**Why:** GPT-5.5 declined 3/5 reps on Experiment 1's "complete, primary-sourced inventory" task. The user's stance: keep it. Same for qwen3-max-thinking — 5/5 refusals at reasoning_effort=minimal is also data (the model's caution amplifies under minimal-effort thinking). Don't rerun expecting different output; don't drop the model; report the refusal rate.

**How to apply:**
- Classifier (`_classify_orphan` in `evaluate.py`) detects refusal-opener language and returns "refusal" regardless of trailing table content. Three tests cover this.
- Manuscript prose uses **declined** for the manuscript-facing column (not "refused" or "other"); "error" is reserved for genuine extraction failures.
- Cost summary table column header is "declined" with caption explanation.
- When the classifier flags a refusal, do not engineer it away with reruns or model swaps — surface it as a finding.
