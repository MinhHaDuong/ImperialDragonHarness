---
name: project-local-routing-llama-server
description: "Ollama is being deprecated for local model routing in favour of llama_server. Don't invest in Ollama-path validation or features; llama_server uses OpenAI-compatible endpoints and inherits the OpenRouter dispatch path."
metadata: 
  node_type: memory
  type: project
  originSessionId: 05a0aece-0924-408e-95ce-e06061312fc0
---

Local model routing is migrating from Ollama (`/api/chat` native) to llama_server (OpenAI-compatible endpoint).

**Why:** User stated 2026-05-21 during 0138/0139 raid wrap-up.

**How to apply:**
- Do not propose empirical validation of Ollama-specific quirks (e.g., where `think` belongs in the request payload — `options` vs top-level). The path is being retired.
- The Ollama branch in `harness.query_model` and `query_ollama_native` is "frozen in working state on the way out" after PR #370. Don't add features there; don't refactor unless deleting.
- llama_server presents an OpenAI-compatible API, so when migration lands, local model IDs should route through `query_single_turn` (the OpenRouter-style path) which already plumbs `seed`, `provider_order` (if applicable), `max_tokens`, `temperature`, and `no_think` via `extra_body.think`. No new `JobSpec` wiring is needed — only a worker dispatch change.
- Affected sweeps (`sweep_regimes_*_local`, `sweep_direct_extract_local`): when their model IDs are repointed at llama_server, behaviour should match the cloud path automatically.

See [[project_padme_local_infra]] for the broader local-first context and [[project_seed_silentdrop_bug]] for the PR #370 fix that closed the Ollama silent-drop.
