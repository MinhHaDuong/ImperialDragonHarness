---
name: feedback-smoke-promote-production
description: "Use `aedist.smoke --promote-as-production` to save smoke calls as production reps without manual rename + strip"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f4537f72-6ba0-4e22-b885-a15b15f10ed9
---

`aedist.smoke` has a `--promote-as-production` flag (since PR #363). With it, smoke output files are named `{slug}-run{N}.json` (worker convention) and the `"smoke": true` marker is omitted. Without it, files land as `{slug}-smoke{N}.json` with the marker.

**Why:** Reruns for production reps (e.g. replacing failed/refusal records in p1_base) need the worker filename convention so `iter_model_replies` ingests them and the .record.json downstream looks like a production rep. Without the flag, the operator does manual rename + JSON-edit-to-strip-marker for each rep. Tedious and error-prone.

**How to apply:**
- For redoing N reps of a model in an existing sweep dir, run
  ```bash
  uv run --project . python -m aedist.smoke \
    --model <model> --calls N \
    --output <sweep-dir> \
    --modules-dir experiments/prompts/modules \
    --models-file experiments/models.yaml \
    --promote-as-production
  ```
  Then run `aedist.extract` + `aedist.evaluate evaluate` to produce CSV + .record.json companions, then `aedist.evaluate assemble` to refresh measurements.jsonl.
- The flag overwrites existing files in the output dir without warning — delete the obsolete records first if replacing specific run numbers (the flag numbers from 1 each invocation).
