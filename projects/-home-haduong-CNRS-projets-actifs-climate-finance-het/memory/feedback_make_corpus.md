---
name: Always say make corpus, never bare dvc repro
description: Never suggest bare dvc repro — always use make corpus (which includes dvc push) or make corpus-sync (which includes dvc pull)
type: feedback
---

Never suggest `dvc repro` or `uv run dvc repro` directly. Always use `make corpus` (on padme) or `make corpus-sync` (on doudou). `make corpus` already does `dvc repro && dvc push` — bare `dvc repro` risks forgetting the push.

**Why:** On 2026-03-24, bare `dvc repro` left pipeline outputs unpushed, breaking `dvc pull` on doudou for 10+ files. The Makefile targets exist precisely to prevent this.

**How to apply:** When the user needs to rebuild pipeline data, say `make corpus` (padme) or `make corpus-sync` (doudou). Never mention `dvc repro` as a standalone command.
