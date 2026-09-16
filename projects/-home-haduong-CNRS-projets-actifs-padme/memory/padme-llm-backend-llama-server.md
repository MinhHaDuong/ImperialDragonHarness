---
name: padme-llm-backend-llama-server
description: "padme local LLM backend is llama-server (llama.cpp) on :8080, not ollama — config + migration gotchas"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9c170357-d13b-4620-ba42-63123659fb6a
  modified: 2026-07-22T19:33:02.125Z
---

The local LLM backend is **llama-server** (llama.cpp), serving an
OpenAI-compatible API. ollama was fully removed in ticket 0010 (2026-06-08).

**Config:**
- systemd unit `tools/llama-server.service` (symlinked into `/etc/systemd/system/`, so a `git pull` in the main checkout updates it). Runs as `User=haduong` — home is `0750` so a service user can't reach the `~/llama.cpp` binary, and `/dev/nvidia*` is world-accessible so no `video`/`render` group is needed.
- Serves **Qwen3.6-35B-A3B** (`/data/models/gguf/qwen/`), port **8080**, `--ctx-size 16384`, `--tensor-split 16,12 --n-gpu-layers 999` across A4000 (16 GB) + 3060 (12 GB). GGUF cache lives under `/data/models/gguf/` (qwen, devstral).
- Binary built with CUDA at `~/llama.cpp/build/bin` (build 9125). Consumer: L3 `reflect-monitoring-history.py` — endpoint/model via `PADME_LLM_URL`/`PADME_REFLECT_MODEL`/`PADME_LLM_CTX`. See [[padme monitoring architecture]].

**Seasonal note:** the author stops llama-server manually during heatwaves
(GPU thermal load). `inactive (dead)` on the unit with nothing on :8080 in
summer is normal at-rest state, not an anomaly — check with the author before
restarting or filing a ticket (2026-07-22).

**Gotchas that cost time (verify before re-tripping):**
1. **ollama GGUF blobs are NOT loadable by llama.cpp** — gemma4's blob failed `wrong number of tensors; expected 1014, got 658`. ollama uses its own internal layout. Migrate from a clean HF GGUF in the cache, not the ollama blob store.
2. **Qwen3 is a reasoning model** — without `chat_template_kwargs:{enable_thinking:false}`, llama-server routes the chain-of-thought into `reasoning_content` and returns **empty `content`** (the token budget is spent thinking). The `/no_think` soft switch does NOT work for it.
3. **llama-server 400s on context overflow** where ollama silently truncated. The L3 agent runs as root and builds a ~10k-token prompt from full dmesg/journalctl; size `--ctx-size` accordingly.
4. **Harness:** long-running GPU/server processes spawned from a Bash call get SIGTERM'd (exit 144) when the call returns — even `run_in_background`. Use **systemd** for a persistent server; use `llama-cli` one-shot (`-no-cnv -n N -p ...`) for load/compat tests.
