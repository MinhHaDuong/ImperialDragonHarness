---
name: Ollama agentic coding experiment
description: Design for benchmarking local LLMs on the project harness using Padme overnight
type: project
---

## Goal

Research experiment: can local LLMs (via Ollama on Padme) autonomously work on braindump tasks using the project's harness? Failure is a valid result — this is benchmarking, not productivity.

**Why:** Evaluate whether the AGENTS.md + runbooks harness transfers to weaker models, and how model size/specialization affects agentic coding quality.

**How to apply:** This is a post-submission project. Design decisions should favor clean experimental methodology over getting work done.

## Padme model inventory (as of 2026-03-18)

- qwen3.5:122b (81GB) — ceiling, overnight only
- qwen3-coder-next (51GB) — large code-specialized
- qwen3.5:35b (23GB) — mid generalist
- qwen3-coder:30b (18GB) — mid code-specialized
- qwen3.5:27b (17GB) — mid generalist
- qwen3.5:9b (6.6GB) — floor/baseline
- Also: devstral-small-2, mistral-small3.2, glm-4.7-flash, nemotron variants

## Experiment design

### Independent variable: model (5 tiers)
1. qwen3.5:9b (floor)
2. qwen3-coder:30b (mid coder)
3. qwen3.5:35b (mid generalist)
4. qwen3-coder-next (large coder)
5. qwen3.5:122b (ceiling)

### Dependent variable: task completion ladder (0–5)
0. Crash — agent loop errors out
1. Lost — incoherent output
2. Understood — correct plan, can't execute
3. Partial — some code, some tests pass
4. Complete — PR-ready, tests green
5. Polished — good commits, clean diff, follows conventions

### Task pool (easiest first)
1. Makefile modularization
2. Polars migration of one script
3. manifest.txt generator
4. Repro package skeleton
5. Skill files decomposition

### Agent loop: open question
- Option A: Aider + Ollama (quick, off-the-shelf, ignores harness)
- Option B: Harness-aware loop (custom, answers real question)
- Could do both: Aider as baseline, harness-aware as treatment

### Logistics
- ~25 cells (5 models × 5 tasks), ~30min each for mid-tier
- Full matrix: 2–3 overnight runs
- Each attempt in a fresh git worktree
- Capture: full conversation log + git diff + test results
- Scoring: manual initially, automate later

## Next steps decided
- Smoke test first: one model + one task to check feasibility
- Then build experiment runner
- Then overnight batch runs
