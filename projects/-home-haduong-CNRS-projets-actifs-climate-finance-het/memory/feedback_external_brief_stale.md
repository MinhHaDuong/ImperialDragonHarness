---
name: feedback_external_brief_stale
description: "Refresh the brief sent to external reviewer models with the latest author decisions, or they review a rule the author already changed"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 99c20e86-e272-4f1d-999a-588c6d03f2c1
  modified: 2026-09-30T20:42:40.707Z
---

The task brief given to external reviewer models (external-peer-review `--task`) must state the author's current decisions. A brief written before a decision keeps describing the superseded design.

**Why:** 2026-09-30, the brief still said "a sampled human review" after the author's autonomy rule; all three wave-2 external reviewers then asked for human audit queues, which had to be rejected wholesale. Also: reasoning models (Kimi K3, Qwen3.8-Max) returned empty reviews at 12k max tokens and the script counted them as "written"; Qwen succeeded at 40k, Kimi failed twice.

**How to apply:** regenerate the brief from the spec index and decision ledger before each external run; check `wc -w` of every review file after the run. See [[feedback_merge_reviews_critically]].
