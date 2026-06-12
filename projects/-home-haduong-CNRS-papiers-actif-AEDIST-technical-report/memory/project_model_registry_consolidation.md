---
name: Model registry consolidation
description: Single models.yaml (52 models) + experiments.toml (routers, model sets) replaced 8 per-sweep YAML files (ticket 0022, completed 2026-04-08)
type: project
---

Ticket 0022 consolidated 8 separate model YAML files into a single registry.

**Architecture (as of 2026-04-08):**
- `experiments/models.yaml` — 52 models, single source of truth. Fields include `router` (openrouter/ollama) and `router_model`.
- `experiments/experiments.toml` — routers, model sets, and sweep configs (`[sweeps.*]` sections). No `sweeps/` directory.
- `src/aedist/harness.py` — shared loader for models, experiments, per-router clients
- `src/aedist/schema.py` — `JobSpec.from_toml_section()` loads sweep config from TOML dict
- `src/aedist/manager.py` — `--sweep NAME --experiments PATH` for TOML-based job fanout
- All 6 query scripts use `--model-set` filtering via harness.py

**Why:** field drift across separate YAML files was unmaintainable; single TOML file prepares for ticket 0011 (retire Makefile dispatch in favor of manager+worker pipeline).

**How to apply:** model additions/changes go in `experiments/models.yaml` only. Sets and sweep configs in `experiments/experiments.toml`. Never create per-sweep YAML files.
