---
name: ticket 0015 pilot status
description: 0015 pilot ready — Qwen3.5-9B operational on PADME; corpus cleaned but 9B has known quality gaps (ticket 0144)
type: project
originSessionId: 03a4885c-8329-44ee-a798-a6edbe7bb0f9
---
Ticket 0015 is the production-stack pilot before sweep 0016. Revamped 2026-05-09.

**Target model:** `unsloth/Qwen3.5-9B` (BF16, ~19GB). **Downloaded** on PADME (`~/.cache/huggingface/hub/models--unsloth--Qwen3.5-9B/`). No bnb-4bit pre-quantized variant exists — `train_lora.py` already has `load_in_4bit=True`, so it quantizes at load time (~5-6GB VRAM, A4000 sufficient).

**Corpus:** multilingual setup — `# language: <iso>` header per chunk, `select_dataset.py --lang fr/en` tie-breaker, translations score authenticity−1. If 0072 not yet merged, build dataset manually from voix-auteur-fr/ + voix-auteur-en/ with headers injected.

**Adapters to save:** `01_training/hdm_fr_q35/` and `01_training/hdm_en_q35/` (separate from Qwen3-0.6B baseline runs in hdm_fr/ and hdm_en/).

**Cleaning quality note (2026-05-15):** The 9B LLM cleaner (Qwen3.5-9B-UD-Q4_K_XL via llama-server) has systematic gaps documented in ticket 0144: verse numbers survive in voix-alienor (25% miss rate), running page headers survive in voix-manne (84% survive), signature fragments in voix-auteur (2311× `Minh`). Fix options: targeted re-clean via OpenRouter stronger model, or prompt additions. Decide before 0016 sweep.

**Why:** Runs 001-003 (Qwen3-0.6B) validated pipeline mechanics. This pilot validates the production stack for sweep 0016.

**How to apply:** Run `scripts/train_lora.py --model unsloth/Qwen3.5-9B --lang fr --output 01_training/hdm_fr_q35` and same for en. Address ticket 0144 cleaning gaps first or accept residual noise.
