---
name: One script produces one table
description: Each table generator is a standalone script with --input and --output, Makefile orchestrates
type: feedback
---

One script produces one table. Each has `--input` (metrics JSON) and `--output` (LaTeX file). The Makefile declares dependencies and orchestrates. No monolithic convert.py that mixes stages.

**Why:** Separation of concerns. Each table depends on a specific sweep's output. If a sweep hasn't run, its table doesn't exist — Make knows that. No hardcoded fallbacks, no TODOs waiting for future data.

**How to apply:** Split convert.py into separate scripts (or subcommands) per table. Each reads one metrics file, writes one .tex file. Makefile wires them together. Both report and slides include the generated tables.
