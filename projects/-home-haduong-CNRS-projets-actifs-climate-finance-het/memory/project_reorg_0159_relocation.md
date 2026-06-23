---
name: project_reorg_0159_relocation
description: Project relocated + GitHub-renamed 2026-06-19 (ticket 0159); engine in projets/, records in papiers/
metadata:
  type: project
---

On 2026-06-19 the climate-finance research programme was relocated and renamed (ticket 0159, now closed). **Many older memories and tracked docs still reference the pre-reorg path/name — treat those references as stale.**

- **Engine repo**: `~/CNRS/papiers/actif/Oeconomia - Climate finance/` → `~/CNRS/projets/actifs/climate-finance-het/` (atomic same-fs `mv`). It's a programme emitting 4 papers, so it now lives under `projets/`, not `papiers/` (one-dir-per-paper).
- **GitHub**: `MinhHaDuong/Oeconomia-Climate-finance` → `MinhHaDuong/climate-finance-het` (old URL still redirects).
- **Submission records** moved out of the repo (`release/` is gone) to untracked `papiers/`:
  - Oeconomia track → `papiers/actif/Oeconomia_Inventing_Climate_Finance/`
  - RDJ4HSS track → `papiers/sent/RDJ4HSS_Curated_Corpus_Climate_Finance/`
  Naming pattern is `<Venue>_WORDS_OF_THE_TITLE`. "Oeconomia"/"RDJ4HSS" survive only as **track/venue** names, never as the engine identity.
- **Build tooling rehomed in-repo**: `release/scripts` → `build/`, `release/templates` → `build/templates/`, process docs (release-journal, revision-runbook, rdj-submission-checklist) → `docs/`.
- **Left unchanged on purpose**: the data/DVC cache dir name `~/data/projets/Oeconomia-Climate-finance/` (regenerable, invisible) and the uv env name `/data/envs/venv/oeconomia`.
- **This memory/transcript cache dir** was moved to the new mangled name and `CLAUDE_MEMORY_DIR` in `.env` updated to match.

Open follow-up: **ticket 0160** — rewrite submission-workflow docs (runbooks + submission-branch/readiness skills) to the `papiers/<state>/<track>/` convention; the submission-branch *mechanism* itself is up for redesign now that records live outside git. See [[project_oeconomia_rr_pipeline]].
