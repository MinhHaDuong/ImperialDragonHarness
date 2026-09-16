---
name: feedback-size-class-per-record-split
description: "A model's size_class can vary across reps in measurements.jsonl; size-keyed sort keys must resolve once per model, not per record, or the model's reps split into non-adjacent groups"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f440e047-9af1-4ea7-b14e-8782336eff40
---

When a plot sorts by model parameter count (e.g. `plot_method_convergence._model_size_b`), resolve the size **once per model** before sorting, not per record. Different reps of the same model can carry different `size_class` values in `measurements.jsonl` (e.g. `qwen3.6-flash` had reps with `'unknown'` → 500 default and reps with `'medium'` → 30), and a per-record sort key splits those reps into non-adjacent positions. When the model's label is then centered on the split y-midpoint, it lands on top of a neighbour's label.

**Why:** Diagnosed in PR #390 (2026-05-21). The visual symptom was `qwen3.6-flash` label overlapping `qwen3.6-35b-a3b`; the cause was upstream data-quality, not plot geometry.

**How to apply:** In any sort/group key derived from a model attribute, build a `model_attr: dict[str, T]` first (using `min`, `max`, most-common, or registry override) and reference that dict in the lambda. Don't do `key=lambda r: f(r["model"], r.get("size_class"))`. See also [[project-seed-silentdrop-bug]] — another case of data-level inconsistency confusing downstream code.
