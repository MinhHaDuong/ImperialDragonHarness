---
name: qwen3.5:9b at F1=0.984 on direct extraction
description: Small local 9B model unexpectedly near the benchmark top on parametric extraction (n=1, needs replication).
type: project
originSessionId: cdaa7a19-9651-4adf-ae9d-cf8d5e977b3b
---
Discovered 2026-04-30 in F1-leaderboard scan of 327 record files: `qwen3.5:9b` (Ollama/Padme, 9.7B dense, Q4_K_M) reaches **F1 = 0.984** on the `direct_extract` regime with `prompt_extract` — within 0.004 of the benchmark-wide best (0.988, DeepSeek V3.2 on decomposed RAG). No RAG, no web, no reasoning, no tools — pure parametric extraction.

**Why:** This single number is the strongest evidence in the corpus that the local-deep-research stack the operator wanted to build (priority 3 in STATE.md, set 2026-04-30) may not be necessary for the **coal-only dev subset**. If the 0.984 reproduces under repeats, "use this 9B as the local extractor" replaces "stand up a deep-research loop with web + reasoning."

**How to apply:**
- Before scoping or building anything in priority 3, repeat `qwen3.5:9b` direct ×3 on the coal-only reference subset and confirm the F1 holds. The current value is n=1.
- If the value does NOT reproduce, the surprise was variance — proceed with deep-research stack as originally planned.
- If it DOES reproduce, the priority-3 ticket scope collapses dramatically — frame the ticket as "validate qwen3.5:9b on coal-only" rather than "build a local deep-research stack."
- Suspicious aspects worth checking on the way: was the `prompt_extract` reference table coal-heavy? Could the 9B have been trained on the same PDP documents (data leakage)? Verify by running on a held-out subset (e.g. only post-2024 plants).
