---
name: Padme: serialize Ollama jobs
description: Workstation is Padme; only one Ollama job at a time to avoid GPU contention
type: feedback
originSessionId: 4c9bcb63-1b61-413b-9058-e5355ab71835
---
This machine is Padme. Only **one Ollama job at a time** — never launch
parallel Ollama-backed runs (e.g. multiple `query_rag.py`, multiple
sweep workers hitting `localhost:11434`, or background + foreground
Ollama work).

**Why:** GPU contention. Multiple Ollama processes thrash the same
GPU/VRAM and either crash, hang, or massively slow each other down.
The user has been bitten by this.

**How to apply:**
- **Always verify GPU availability before dispatching any Ollama-bound
  job** — `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv`
  plus `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`.
  If a process is already holding VRAM, do not launch; wait or skip.
- Before launching any Ollama-bound task, check whether another is
  already running (`pgrep -af ollama`, `curl -sf localhost:11434/api/ps`,
  inspect background bash tasks).
- If a sweep includes an Ollama model and the GPU is busy, sidestep it
  by pre-writing sentinel JSONs in the output dir so `should_skip`
  fast-forwards over it; do not stop the whole sweep for one model.
- For multi-model sweeps (e.g. ticket 0021's `qwen3.5:2b` + `qwen3.5:4b`),
  run them **sequentially**, not in parallel.
- The "parallelize API calls" rule explicitly does NOT apply to Ollama —
  parallelism is fine for OpenRouter/OpenAI/Mistral cloud APIs but NOT
  for local Ollama on Padme.
- If the orchestrator wants to run multiple tickets that each touch
  Ollama, group them into a serial wave, not parallel.
