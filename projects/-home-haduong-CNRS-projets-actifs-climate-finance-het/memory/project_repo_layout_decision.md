---
name: project_repo_layout_decision
description: "Repo-layout adjudication (2026-07-10) — deliverables/ ratified, src/ declined, shared harvest/index → libs/ for AEDIST"
metadata: 
  node_type: memory
  type: project
  originSessionId: ea1cbb06-91f7-47d0-98e2-86ddd1fab4bd
---

Author-adjudicated 2026-07-10 (tracker 0223, doc `docs/repo-layout.md`, canonical rules `.claude/rules/architecture.md` under 0221):

- **`deliverables/` per-paper Quarto — RATIFIED.** Each paper/slide deck becomes a self-contained folder with its own `_quarto.yml` + vars + `.mk`, shared assets in `deliverables/_shared/`. Kills the exclusion-mask profile files (`_quarto-manuscript*.yml`). Slides are deliverables, not papers (peers). Replaces the one-`content/` multi-doc project. Do post-resubmit (0226).
- **`src/climatefinance/` — DECLINED.** Keep the existing library convention: `_`-private modules + `pipeline_*` loaders in `scripts/`, `libs/` for cross-repo sharing. Code reorg (0225) = phase sub-grouping (`scripts/{harvest,analysis,figures,qa}/`) + the five audit extractions landing as plain modules *inside their phase subdir* — no top-level package, no `python -m` flip.
- **Shared corpus harvest + indexing → `libs/`, not `src/`** (driver: **AEDIST**, `~/CNRS/papiers/actif/AEDIST-technical-report/`). Cross-repo sharing is what `libs/openalex-corpus` exists for (0170) — AEDIST is its first external consumer. `src/` is repo-internal and wouldn't help AEDIST. Harvest conventions already in the package; indexing (deliberately excluded — "ships no model choice") is the gap AEDIST motivates. Seed: ticket 0229.

Scheduling (two axes, different timing): the **data axis** (0221 tracker, child 0218; 0222 landed 2026-07-10) is **en cours** — a parallel session is actively executing it. The **code+prose axis** (0223/0225/0226) + the AEDIST seed (0229) are **post-Œconomia-resubmit** — they destabilize the resubmission build machinery for no deadline payoff, so they carry `Label: deferred`; the data-axis tickets do not. 0224 (my duplicate data-reorg tracker) was closed as a dup of 0221/0218/0222. Watch for git-erg optimistic-ID collisions under parallel sessions: my AEDIST seed first got 0227, collided with the parallel session's 0227, renumbered to 0229. See [[project_reorg_0159_relocation]] for the earlier relocation, [[feedback_atomic_tickets_validation_units]] for one-validation-unit discipline.

The rule that decides code placement: **imported → library (stays `scripts/` `_`-private or `libs/` if cross-repo); invoked-only → entry point; a script that leaks a helper → extract the helper.** Layering invariant: `deliverables → scripts/figures → scripts/analysis (compute)`, never backward — a compute module must not import a plotter (architecture.md rule 4).
