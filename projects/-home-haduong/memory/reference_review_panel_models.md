---
name: reference_review_panel_models
description: "How to invoke each off-harness reviewer (local Qwen on padme, Codex Luna/Terra/Sol) and what a 7-model panel run on 2026-09-24 showed about each"
metadata:
  node_type: memory
  type: reference
  originSessionId: 34222eaf-59c7-434b-b131-e607cba6fdc2
  modified: 2026-09-24T05:51:48.631Z
---

**Invocation.**
- Local: `llama-server` on padme, `http://127.0.0.1:8080/v1/chat/completions`, alias `qwen3.8-27b`, **one slot** (calls serialize; another session queues behind you). It thinks at length: a 28-line diff took 9 784 completion tokens. With `max_tokens` 6000 it returned empty `content` (the budget ran out mid-reasoning) and still exited 0. Use ≥ 32k and check `finish_reason == "stop"`.
- Codex: `codex exec -m <model> -c model_reasoning_effort=medium -s read-only --skip-git-repo-check -o out.md "<brief>"`. Model ids from `~/.codex/models_cache.json`: `gpt-6-luna`, `gpt-5.6-terra` (no 6 version), `gpt-6-sol`. "Astra" (`gpt-6-astra`) is not one the author means.
- Claude tiers: `Agent` with `model: haiku|sonnet|opus`.

**What the panel showed (3 PRs: one code fix, two ticket specs; same brief to every model).**
- Opus: most thorough. It opened the tree and found consumers the ticket missed (`ZOTERO_API_KEY` in a `.mk`, `OPENROUTER_API_KEY` readers).
- Sonnet: the single most valuable lead. It pointed at 0679's backup file, which reversed the ticket's history claim.
- Sol, Terra, Luna and Opus independently converged on the same redesign of the harness ticket. Four decorrelated reviewers agreeing is a strong signal.
- Terra: sound findings, inflated severity (it rated a minor edge case "blocking").
- Luna: one factual error. It claimed duplication that the diff had already removed.
- Haiku: shallow, and its "blocking" finding was about pre-existing code rather than the diff.
- Local Qwen: once given the budget, it found a real edge case (an empty keystore value) that only Opus had also seen. On specs it produced many generic "unsupported claim" items.

Related: [[feedback_adversarial_pair_verification]].
