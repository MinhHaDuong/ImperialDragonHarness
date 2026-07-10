---
name: feedback_reorg_tracker_first_class_guard
description: "Multi-ticket reorg needs a tracker filed BEFORE executing, and guards must be class-level (keyed on producer phase), not per-file whitelists"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 18f92418-6ed9-421b-ae80-1862b37a91a4
---

A layout reorganization (2026-07-10, tickets 0208/0219/0222, tracker 0221) taught two process lessons that generalize past this repo.

**Why:** The repo is organized along **four logics that must each stay coherent and not bleed into one another** — *build* (Makefiles / workpackage `.mk`s), *layout* (directories), *data-analysis* (dataflow phases 1→4), *tracking* (tickets). The author surfaced this frame through terse Socratic prompts, correcting me off the wrong axis (DVC-vs-gitignored *governance*) onto the right one (**layout mirrors dataflow phase**). The load-bearing convention now lives in `.claude/rules/architecture.md` (§ Data location, § Artifact homes by phase): `data/catalogs/` = Phase-1 corpus; `data/derived/` = Phase-2 derived; flat, **not** mirrored to workpackages (mirroring couples layout↔build and breaks on cross-workpackage files like `tab_pole_papers.csv`).

**How to apply:**
- **File the tracker BEFORE executing a multi-ticket reorg, not after.** Executing piecemeal without the tracking logic let the reorg ship *incomplete* — a per-file guard silently missed a third leak (`data/catalogs/communities.csv`). The tracker is what forces the completeness audit. When the author asks "did we open a ticket for this?", the honest answer is usually no, and the fix is a retroactive tracker + a completion child.
- **Make guards class-level, keyed on the producer, not a basename whitelist.** 0219's guard pinned two filenames and missed the class; 0222 rewrote it to parse the Makefile and fail if *any* target produced by a Phase-2 script (`analyze_/compute_/plot_/export_/summarize_/build_het`) resolves under `data/catalogs/`. A new leak now fails without editing the test.
- **Phase-by-filename-prefix is a heuristic with exceptions** (`compute_reranker_calibration` is Phase-1; `qa_embeddings`/`qa_detect_type` are Phase-2), and a Makefile-parsing guard is blind to scripts with no Make target — tracked as the guard's known coverage boundary ([[0227]] under tracker 0221).

See also [[project_writing_build_phase_separation.md]], [[feedback_decide_dont_micromanage.md]].
