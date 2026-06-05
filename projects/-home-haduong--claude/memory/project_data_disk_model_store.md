---
name: data-disk-model-store
description: "Big artifacts (LLM weights, GGUF, datasets) go to /data/models — never the homedir"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2e3a435d-3125-4f64-943a-899d61962db7
---

On padme, large model files (GGUF, safetensors, ollama blobs) live on the
dedicated `/data` disk under `/data/models/{gguf,ollama,safetensors}/` —
never in the homedir (author directive, 2026-06-05, after a 14 GB GGUF
download was started in `~/llama.cpp/models/`).

**Why:** homedir is for code and config; `/data` is the bulk store.

**How to apply:**
- Download GGUFs to `/data/models/gguf/<family>/` (that subdir is
  user-writable even though `/data/models` itself is root-owned).
- `LLAMA_CACHE=/data/models/cache` is the intended llama.cpp cache; if it
  errors "failed to create cache directory", the subdir is missing and needs
  `sudo mkdir + chown` — ask the author to run it, do NOT redirect the cache
  to the homedir as a workaround.
- Serve with an explicit `-m /data/models/gguf/...` path rather than `-hf`
  auto-download where possible.
