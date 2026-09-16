---
name: project-phase-build-layout
description: "Build is split one .mk per phase (2026-06-04, tickets 0405/0406) — acquire/score/render + root staleness/world; old root verbs are gone"
metadata: 
  node_type: memory
  type: project
  originSessionId: 67279a06-6365-498b-a9e8-12f7c9c12264
---

Since 2026-06-04 (tickets 0405/0406, PRs #690–#704) the build is phase-stratified:

- P1 `experiments/acquire.mk` — money-gated API sweeps, ALL targets .PHONY, invoke as `make -C experiments -f acquire.mk <sweep>` (cwd contract: ../.env, experiments.toml, jobs/)
- P2 `experiments/derived/score.mk` — `measurements.jsonl`, `exp2_mart.jsonl`, cross-evals; `rebuild-measurements` is deliberate-and-reviewed
- P3 `experiments/render.mk` — all figures/tables/macros → `report/inputs/generated/` (single tree; `slides/inputs/generated/` retired, its two files renamed `macros_slides.tex` / `tab_exp2_2x2_fr.tex`)
- P4 `report/Makefile`, `slides/Makefile` — artifacts-only writing builds
- Root: dev loop + exactly two cross-phase entries — `make staleness` (safe dry-run report) and `make world` (full P2+P3+P4 re-run, dirty-tree-guarded, NEVER run casually: rewrites committed scores, review git diff). P1 excluded from both.

Old root verbs `tables`/`figures`/`select`/`census`/`measurements` are DELETED — do not suggest them. Boundary guards: test_render_build_clean_room, test_score_build_no_acquire, test_acquire_all_phony, test_root_no_cross_phase_prereq, test_no_tracked_ignored_files. Artifact policy manifest: docs/pipeline-phases.md. Open follow-ups: 0414 (_NEEDS_ENV), 0417 (orphan P3 artifacts), 0360 (world content-diff oracle). See [[feedback-ticket-id-collision-check]].
