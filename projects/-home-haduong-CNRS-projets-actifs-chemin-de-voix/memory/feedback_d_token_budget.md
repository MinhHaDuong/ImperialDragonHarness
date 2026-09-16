---
name: feedback_d_token_budget
description: D-notice needs 1500 max_new_tokens — 800 truncates 4th/5th translations
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a11b63b8-e69e-40d9-aaaa-44a002663528
---

When the model generates N parti pris + N translations, it produces markdown headers and per-section commentary (not just the translations). Budget: ~150 tok for the list + ~200 tok × 5 translations + ~100 tok commentary = ~1400 tok minimum.

**Why:** 800 tokens seemed sufficient (5 × 80 tok ≈ 400 + overhead), but the model adds `### Parti pris N`, `*Commentaire: ...*`, and structural markdown that doubles the token count.

**How to apply:** Use `max_new_tokens=1500` for any D-variant or multi-output enumeration prompt. 300 is fine for A/C single-translation prompts.
