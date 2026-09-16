---
name: Long-running corpus jobs — foreground, not background
description: How to handle make/dvc corpus stages — run in foreground so user sees live progress, never in background
type: feedback
---

Run corpus/DVC pipeline stages (`make check`, `dvc repro`, enrich scripts) in **foreground**, never with `run_in_background: true`.

**Why:** The user needs real-time visibility into long-running corpus jobs to monitor progress and `^C` if stuck. Running in background hides output entirely — the user only sees results after completion, defeating the purpose. Previous oscillation between extremes (refusing to run `make` at all vs. running everything in background) caused repeated frustration.

**How to apply:**
- `make` and `dvc repro` commands: always foreground, so output streams live.
- Do NOT avoid running `make` — it is safe to run. The user wants you to run it, just visibly.
- Do NOT use `run_in_background` for corpus stages — the user cannot monitor progress that way.
- Short commands (`make check-fast`, `make lint`) are fine either way.
- If a job is expected to run very long (>30 min), mention the estimate and let the user decide, but default to foreground.
