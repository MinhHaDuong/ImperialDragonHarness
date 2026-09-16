---
name: seed silent-drop bug in JobSpec
description: seed=42 in 57 sweeps was silently dropped by Pydantic — never reached the API
type: project
originSessionId: 369b9a4c-0683-4e4d-b0db-88137a73b395
---
`seed`, `provider_order`, `max_tokens`, and `num_ctx` are not declared fields in `JobSpec`. Pydantic silently drops unknown fields on load. Result: 57 sweeps set `seed = 42` believing it controlled MoE reproducibility — it never reached `build_api_kwargs`.

**Why:** Ticket 0139 tracks the fix: add missing fields, add `extra="forbid"` to `JobSpec.model_config`.

**How to apply:** Do not assume seed was honoured in any pre-0139 run. MoE model results (DeepSeek V3.2, Qwen3 MoE) from existing sweeps are uncontrolled for seed and provider routing. Flag when interpreting variance in those runs.
