---
name: feedback_d_seed42_collapse
description: "seed=42 collapses D-notice (5 parti pris) to 1 translation — use D_SEEDS=[137,271]"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a11b63b8-e69e-40d9-aaaa-44a002663528
---

For prompts that ask the model to generate N contrasting outputs (e.g. "5 parti pris littéraires"), seed=42 causes the model to pick one and produce only that one instead of all 5. Seeds 137 and 271 reliably produce all 5.

**Why:** seed=42 with a meta-cognitive framing ("parti pris que ce passage t'inspire") triggers a collapse to a single "best choice" rather than the enumerated list. Reproduced consistently across temperatures (0.6 and 0.8).

**How to apply:** Define `D_SEEDS = [137, 271]` (or similar) for any generation task using multi-output enumeration prompts. Do not use seed=42 for D-variant or similar structured multi-output calls.
