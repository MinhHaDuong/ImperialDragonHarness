---
name: feedback-pydantic-forbid-extras-audit
description: "Before flipping `extra=\"forbid\"` on a Pydantic model that loads external configs, grep the configs for every key used and reconcile against declared fields. The flip turns each unknown key into a ValidationError at load — the audit converts \"medium risk\" into \"small, well-bounded change.\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 05a0aece-0924-408e-95ce-e06061312fc0
---

When adding `model_config = ConfigDict(extra="forbid")` to a Pydantic `BaseModel` that loads external configs (sweep YAML/TOML, user-edited files), audit first.

**Procedure:**
1. Grep every key used in the config source (e.g., `experiments.toml` `[sweeps.*]` blocks).
2. Reconcile against the model's currently-declared fields.
3. For each unknown key, decide: declare it as a field, strip it before validation (e.g., manager-owned keys in `_remap_sweep_fields`), or flag as a config error.
4. Only then flip `extra="forbid"`.

The just-completed primary sweep is the live canary — it must still load cleanly after the flip.

**Why:** PR #370 / ticket 0139 — advisor flagged this as the real risk gate ahead of the agent's first attempt. Audit found 58/63 sweeps clean; the 5 failures were pre-existing missing-required-fields in verification/fusion sweeps not routed through the manager. The flip became a small, well-bounded change instead of a config-load blowup.

**How to apply:**
- Applies any time you add `extra="forbid"` to a Pydantic model that loads user-edited configs.
- For internal data structures (output records, computed objects), `extra="forbid"` is less load-bearing — the boundary discipline matters most where users can typo.
- Pair the flip with a regression test that asserts the model rejects an unknown key (see `tests/test_jobspec.py::TestJobSpecForbidExtras`).
