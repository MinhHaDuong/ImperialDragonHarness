---
name: Padme local AI infrastructure
description: Available local services on Padme for AI tasks — GROBID, Ollama, GPUs
type: reference
originSessionId: 17bdab73-2acc-4097-a23b-79296220e6c8
---
**This workstation IS Padme.** When a ticket says "on Padme", the commands run locally — no ssh, no tailscale. Verify with `hostname` if unsure; check Ollama with `curl -sf http://localhost:11434/api/tags`.

Padme has local infrastructure for running AI tasks without cloud APIs:
- **GROBID 0.8.1**: `podman start grobid` → port 8070. Good for PDF table extraction, even Vietnamese government docs.
- **Ollama 0.22.0** (updated 2026-04-29): port 11434. Models include qwen3.5 (0.8b–122b), mistral-small3.2, glm-4.7-flash, devstral-small-2. `qwen3.6:35b` pulling as of 2026-04-29 (ETA >1h).
- **GPUs**: RTX A4000 (16GB) + RTX 3060 (12GB)
- **Container runtime**: podman (not docker)

**Why:** User prefers local-first pipelines — zero cloud cost, no API key dependencies for conversion/scoring tasks.

**How to apply:** Default to local tools (GROBID, Ollama) for new scripts. Reserve cloud APIs (OpenRouter, OpenAI) for tasks that specifically need frontier models.
