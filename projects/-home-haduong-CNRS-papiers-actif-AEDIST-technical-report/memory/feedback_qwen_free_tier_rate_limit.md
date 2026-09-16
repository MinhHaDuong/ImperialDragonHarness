---
name: qwen-free-tier-rate-limit
description: "Alibaba's free-tier qwen/qwen3.6-flash:free (and similar :free models) on OpenRouter rate-limits within seconds of a successful call. Plan serial-with-pause access, never parallel."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de20a516-38a3-4ccc-b4a4-236f555d39aa
---

Empirically observed during ticket 0198 topup (2026-05-21):
- A single direct probe of `qwen/qwen3.6-flash` returns 200 OK.
- The same model called by the worker seconds later returns 429.
- The 429 window persists for ~10 min between successful calls.
- Even serial-with-60s-pause script hit 429 on 3 of 4 attempts.

`deepseek/deepseek-v4-flash:free` showed the same behaviour earlier in
the session.

**Why:** Alibaba and DeepSeek expose free tiers via OpenRouter with very
narrow per-second / per-minute caps that don't show up as a clean
"retry-after" header — the upstream just returns 429 with a generic
"temporarily rate-limited upstream" message.

**How to apply:** For any `*:free` OpenRouter model in a sweep:
1. Add `--retry-pause 180+` with `max-retries 4+` in any custom drain script.
2. Don't include `*:free` models in parallel-worker drains alongside
   paid models — they'll burn worker slots and exit the queue on 429.
3. For pooling with historical data, prefer the paid variant if it
   still resolves on OpenRouter (e.g. `qwen/qwen3.6-flash` without
   `:free` still resolves and is much less rate-limited).
4. If a single rep is enough (reasoning-token characterization), use
   `aedist.smoke --calls 1 --promote-as-production` instead of the
   worker — easier to space attempts.

This bug is separate from the worker-on-429 bug ([[worker-exits-on-429]])
— even after that's fixed, free-tier rate limits will still make
parallel runs problematic.

Related: [[padme-ollama-serial]] for the local-side serialisation
constraint.
