---
name: llama-server workload on padme
description: Two llama-server instances on padme run a long OCR-cleaning workload — do not interfere
type: project
originSessionId: 8961e319-d8cd-487c-a29e-93bf635cc3d1
---
Two `llama-server` instances on padme (ports 8080 and 8081) serve Qwen3.5-9B-UD-Q4_K_XL with 64K ctx, q4_0 K/V cache, one per GPU (RTX A4000 + RTX 3060). Workload is OCR text cleaning — runs unattended.

**Why:** the user explicitly said "don't interfere with the runs" (2026-05-11). These are long batch jobs, not interactive sessions.

**How to apply:** do not restart, benchmark, hit endpoints, or change config of these servers without asking. If asked about tuning (f16 vs q4_0 K/V, ctx size, etc.), answer analytically — don't offer to "just try it" on the live instance. For OCR cleaning the contexts are short-to-medium (~500–2000 tokens), so K/V cache tuning matters less than it does at 64K.
