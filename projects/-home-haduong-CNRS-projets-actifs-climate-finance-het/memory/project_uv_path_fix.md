---
name: UV non-interactive PATH fix (Makefile idiom)
description: Repo-wide pattern for making `uv` resolvable in non-interactive shells (ssh, cron, systemd) via Makefile variables + PATH export
type: project
originSessionId: ef11c666-f3b1-4055-8da9-0a38cfc505eb
---
PR #719 (merged 2026-04-21, commit 47b79da, ticket 0087) installed this stanza in the top-level `Makefile`:

```make
UV      ?= uv
UV_RUN  ?= $(UV) run
export PATH := $(HOME)/.local/bin:$(PATH)
```

All 99 `uv run ...` sites in `Makefile` (79) and `divergence.mk` (20) were rewritten to `$(UV_RUN) ...`.

**Why:** `ssh padme 'make null-model'` died four times with `uv : commande introuvable` because non-interactive shells don't source `.bashrc`. The PATH export fixes the whole class (ssh, cron, systemd) in one place.

**How to apply:** any new Makefile or `.mk` must use `$(UV_RUN)`, not raw `uv run`. Any shell script meant to run via non-interactive SSH must start with a PATH guard: `command -v uv || export PATH="$HOME/.local/bin:$PATH"`. Release templates (`release/templates/Makefile.*`) are tracked under follow-on ticket 0088 — apply the same discipline when touching them.

**Verification probe (gold standard):**
```
ssh padme 'cd ~/Climate_finance && timeout 8 make content/tables/tab_null_L1.csv 2>&1 | head'
```
Pre-fix: `uv : commande introuvable` (exit 127). Post-fix: Python script runs, produces INFO log lines, killed by timeout (exit 124).
