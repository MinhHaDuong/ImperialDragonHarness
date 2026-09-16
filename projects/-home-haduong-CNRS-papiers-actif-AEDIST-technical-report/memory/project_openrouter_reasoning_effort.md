---
name: project-openrouter-reasoning-effort
description: "OpenRouter reasoning_effort semantics are counterintuitive — \"minimal\" turns reasoning ON; absence turns it OFF"
metadata: 
  node_type: memory
  type: project
  originSessionId: c5cea9fc-7d2c-4f74-9ce5-4a0a43ce75c3
---

For models routed through OpenRouter (`extra_body={"reasoning": {"effort": ...}}`), the empirically-observed semantics on 2026-05-21:

- **No `reasoning_effort` sent**: provider runs in fast-mode; `usage.completion_tokens_details.reasoning_tokens = 0`. Tested on `qwen3-max-thinking`, `mistral-small-2603`, `claude-opus-4.6`, `qwen3-max`.
- **`effort = "minimal"`**: turns reasoning **ON**, briefly. For `qwen3-max-thinking` on a trivial arithmetic prompt: 417 reasoning tokens (vs 0 with no effort). For the real Vietnam plant prompt: 2,199 reasoning tokens, *and the model refused the task* on epistemic grounds.
- **`effort = "minimal"` on a non-thinking model** (`qwen/qwen3-max`): no-op, still 0 reasoning tokens.

**Why:** "Minimal" is the lowest level of the OpenRouter `reasoning.effort` enum (minimal / low / medium / high). It's not an "off" switch — it's "thinking on, brief". The models.yaml comment at line 955 claiming `reasoning_effort = "minimal"` "mirrors the no_think discipline" is empirically backwards for thinking-capable models.

**How to apply:**
- When designing a "no reasoning" sweep on OpenRouter models, **do not send any `reasoning_effort`** — leave it absent. Sending `"minimal"` will turn reasoning on.
- When designing a "compare reasoning depths" sweep, the four discrete levels (minimal / low / medium / high) all imply reasoning is on; the off-state is "no key sent".
- For Anthropic's extended thinking: not exposed via OpenRouter's unified `reasoning.effort` field at all. `claude-opus-4.6` via OpenRouter shows 0 reasoning_tokens regardless of effort. Use the Anthropic-direct route (`adapter_anthropic` / `extra_body.thinking`) if you need to probe Claude reasoning.
- For Ollama-native: use `options.think: false` to suppress; absence leaves thinking-capable models running with thinking on.

Captured during PR #379 / ticket 0197 probe. Source data: `/tmp/probe_reasoning_usage.json`, `/tmp/probe_reasoning_real_prompt.json` (ephemeral). See [[project-exp1-done]] for the manuscript impact (Annex A "Reasoning" column dropped because labels reflected metadata, not measurement).
