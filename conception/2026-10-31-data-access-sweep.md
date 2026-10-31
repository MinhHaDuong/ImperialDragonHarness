# Data-access sweep for the DATASETS_DIR migration (2026-10-31, read-only)

## Header

- **Hosts reached:** padme (local) and doudou (`ssh -o BatchMode=yes doudou`, hostname answered `doudou`). Both were reached and scanned.
- **Method:** for every repo, `git grep --untracked -I -i -P` over tracked and untracked files. This avoids `.git`, nested worktrees and gitignored bulk data. Then a second pass reads the gitignored config files (`.env*`, `.envrc`, `.dvc/config*`, `*.local.mk`, `config.local*`, depth ≤4). Third, a separate pass looks for dataset folder names (`datasets/external|ours`, `Archives CIRED`, `ISTEX/`, `VIET DATA`, `Enerdata`, `GHCND`, …). Fourth, a `find -type l -lname '*data*|*RePEc*|*mirrors*'` symlink pass runs over `~/.agents`, `~/CNRS` and the `~/data` repos. No ripgrep globs were used.
- **Counting:** "strong" hits contain a real storage path or an env var. "Weak" hits are bare-word matches (`repec`, `'datasets'`) and are not storage access, so they are left out of the E/C/D/F columns.
- **Repos enumerated on padme (46 git dirs):**
  - Scanned (20):
    - `~/.agents`
    - `~/CNRS/code/{arena, DOIfetch, git-erg, search-works-for-zotero, search-works-for-zotero/fork, zoteus}`
    - `~/CNRS/papiers/actif/{AEDIST-technical-report, fuzzy-corpus, sen-causal-reading}`
    - `~/CNRS/projets/actifs/{cadens, chemin-de-voix, climate-finance-het, JETP-observer, livre-milliards-climat, padme}`
    - `~/data/search-works-for-zotero`
    - `~/data/t0643/fork`
    - `~/data/projets/zoteus-bench/{review-pr3, stock-v1120}`
  - Not content-scanned:
    - `~/.agents/.worktrees/*` (2, branch worktrees)
    - `arena/repos/*` (4) and `arena/workloads/*` (10): benchmark snapshots. Only their ignored config files were read; they are FROZEN.
    - `search-works-for-zotero/zotero-work{,/document-worker}`
    - `~/data/ladder/zotero-6012/*` (8, upstream Zotero source)
- **Repos enumerated on doudou (64 git dirs):**
  - Scanned (52):
    - `~/.agents`
    - `~/CNRS/code/`: activity_report_writer/{activity-analysis, PublicationAnalysis, ribac-check}, askMinh, attic/aedist-2026-04, "carto chercheurs département SSM IP", Costs-and-Benefits-Cofiring-VN, DOIfetch, DoiHarvest, fs-housekeeper, git-erg, "Household electricity", llm_benchmarks, maiba, "Music Library Clinic", natu, search-works-for-zotero{, /fork, /fork-stock}, ThinkTanksSurveyor, translatorfactory/translators, VinaPyPSA, VN-Power-Scenario, vnpypsa
    - `~/CNRS/html`
    - `~/CNRS/papiers/`: actif/{Gavard Scotch 2026…, livre-milliards-climat, sen-causal-reading}, grenier/Hoai Son 2021…/src
    - `~/CNRS/projets/actifs/`: aedist, archiveCIRED, cadens, chemin-de-voix, CIRED.digital{, /cired.digital}, climate-finance-het, corpus-access-bench, "Fuzzy Corpus", JETP-observer, klem-closure-python{, /upstream}, ODUM, padme, polycentric_activity, zoteus-fts5{, /fork}
    - `~/CNRS/projets/placard/`: "CIRED connect/CIRED_alumni_directory", replicator
    - `~/data/projets/zoteus-bench/`: fork-0091, smoke-1.10.0/zoteus
  - Not content-scanned:
    - `~/data/datasets/external/RePEc/wfo`: a git repo inside the RePEc mirror. It is dataset content (18,877 word hits).
    - `~/data/golden-fixture-scratch/pytest-tmp/*` (7)
    - `~/data/scratch-fold-sweep/*` (3)
    - `~/data/scratch-zotero-mcp/*` (2)
- **Positive controls:**

  | Control | Host | Result |
  |---|---|---|
  | `~/.agents/scripts/transcript_spool.py:31` (`/data/datasets/ours`) | padme | FIRED |
  | same file, repo content scan | doudou | FIRED |
  | `~/.config/systemd/user/cadens-harvest.service:6` (`CADENS_RAW_DIR`) | padme | FIRED |
  | `~/.bashrc:156` (`export CADENS_RAW_DIR`) | doudou | FIRED |
  | `~/.config/environment.d/huggingface.conf:1` (`HF_HOME`) | doudou | FIRED |
  | DVC-config class (`JETP-observer/.dvc/config:5`) | both | FIRED |
  | ignored-`.env` class (`cadens/.env`) | both | FIRED |
  | symlink class (padme: `AEDIST…/experiments/data/rag_corpus`; doudou: 1,602 links) | both | FIRED |
  | crontab readable (padme: no crontab; doudou: one mutt reminder, no data path) | both | FIRED |

  No search class is blind.

## Per-project table, strong hits (E=EXEC, C=CONFIG, D=DOC, F=FROZEN)

The counts are automatic. Path rules decide the class: `tickets/closed`, `memory/journal`, `bench/results`, `measurements/`, `output/`, logs and arena docs/configs are FROZEN. EXEC counts include docstring usage lines and test fixtures; the site lists below give only the load-bearing ones.

| Host | Project | E | C | D | F | Areas touched by E+C |
|---|---|---|---|---|---|---|
| both | `~/.agents` (harness) | 28 | 1 | 55–56 | 30–37 | **ours** (agent-sessions) |
| both | `CNRS/projets/actifs/cadens` | 26–27 | 4–5 | 7–8 | 32 | **ours** (agent-sessions), projets (legacy) |
| doudou only | `CNRS/projets/actifs/archiveCIRED` | 4 | 1 | 2 | 2 | **ours** (Archives CIRED numérisées) |
| both | `CNRS/projets/actifs/climate-finance-het` | 25 | 14 | 40 | 78 | **external** (RePEc), projets, cache/envs, models; indirect **ours** (ISTEX) on doudou |
| both | `CNRS/projets/actifs/chemin-de-voix` | 35–36 | 0 | 3–8 | 113 | projets, models |
| both | `CNRS/projets/actifs/JETP-observer` | 2–4 | 2–3 | 34–36 | 1–3 | projets (DVC), models |
| both | `CNRS/projets/actifs/padme` | 50–56 | 2 | 9 | 472–501 | models, cache |
| padme | `CNRS/code/arena` | 8 | 0 | 0 | 150 | models, arena-store, cache |
| both | `CNRS/code/search-works-for-zotero` | 30–40 | 0 | 30–33 | 865–889 | ~/data scratch, projets/zoteus-bench, cache |
| padme | `~/data/search-works-for-zotero` | 11 | 0 | 3 | 313 | projets/zoteus-bench, ~/data scratch |
| padme | `CNRS/papiers/actif/AEDIST-technical-report` | 0 | 1 | 0 | 0 | projets (comment only) |
| doudou | `CNRS/projets/actifs/polycentric_activity` | 2 | 0 | 5 | 0 | ~/data other (`~/data/Zotero`, `~/data/corpus-complexite`) |
| doudou | `CNRS/projets/placard/CIRED connect/CIRED_alumni_directory` | 1 | 0 | 0 | 0 | none (URL `edirc.repec.org/data/…`, false positive) |
| both | sen-causal-reading, fuzzy-corpus / Fuzzy Corpus, activity-analysis, maiba, aedist, zoteus-fts5{,/fork}, sfz fork/fork-stock, translatorfactory, replicator, Gavard Scotch | 0 | 0 | 0–13 | 0–5 | weak (word-only) or DOC only |
| both | all other scanned repos | 0 | 0 | 0 | 0 | — |

Ranges are padme–doudou differences between the two checkouts.

### EXEC + CONFIG sites that touch the datasets area (the migration target)

**Harness `~/.agents`** (identical on both hosts):
- `scripts/transcript_spool.py:31` EXEC: `OURS_PROBE = Path('/data/datasets/ours')`
- `scripts/transcript_spool.py:32` EXEC: `STORE = Path('datasets/ours/agent-sessions')`
- `scripts/transcript_spool.py:38-39` EXEC: `IDH_ARCHIVE_ROOT` override
- `scripts/transcript_spool.py:41` EXEC: `return OURS_PROBE / 'agent-sessions'`
- `scripts/transcript_spool.py:42` EXEC: `return Path.home() / 'data' / STORE`, the doudou fallback `~/data/datasets/ours/agent-sessions`
- `tests/test_transcript_archive.py:133,136,137` EXEC (test): asserts the `home/data/datasets/ours/agent-sessions` and `ours/agent-sessions` defaults
- These scripts take the root from `transcript_spool` or `IDH_ARCHIVE_ROOT` and hold no literal path of their own: `scripts/pi-subagent-link:63`, `scripts/trace_timeline.py:562/568` (padme), `:539/545` (doudou)
- `scripts/systemd/transcript-archive.service` is the template. It holds no path, only a mention in its description.

**cadens.** The code is env-driven: `src/cadens/harvester/raw_store.py:20` reads `CADENS_RAW_DIR` and has no hardcoded path. The values live in:
- padme `.env:1` CONFIG (gitignored): `CADENS_RAW_DIR=/data/datasets/ours/agent-sessions/raw`
- padme `.env:2` CONFIG: `CADENS_CCR_DIR=/data/datasets/ours/agent-sessions/cadens/padme/claude-ccr`
- doudou `.env:1` CONFIG: `CADENS_RAW_DIR=/home/haduong/data/datasets/ours/agent-sessions/raw`
- doudou `.env:2` CONFIG: `CADENS_CCR_DIR=/home/haduong/data/datasets/ours/agent-sessions/cadens/doudou/claude-ccr`
- `.env.example:2,4` CONFIG (tracked): padme paths `/data/datasets/ours/agent-sessions/...`
- doudou `.envrc:1` CONFIG (gitignored): `export CADENS_RAW_DIR="${HOME}/data/projets/cadens/raw`. This is the legacy path and contradicts `.env`. `direnv` is not installed on doudou.

**archiveCIRED** (doudou only; no padme clone):
- `Makefile:1` CONFIG: `ARCHIVE ?= /home/haduong/data/datasets/ours/Archives CIRED numerisées`
- `src/build_doc_index.py:356` EXEC: same path as the argparse default
- `src/build_file_index.py:63` EXEC: same
- `src/build_index.py:664` EXEC: `_archive_root: Path = Path("/home/haduong/data/datasets/ours/Archives CIRED numerisées")`
- `src/build_index.py:674` EXEC: same as the argparse default

**climate-finance-het** (both hosts):
- `scripts/catalog_rel_eds_repec_handles.py:149` EXEC: `ap.add_argument("--mirror", default="/data/mirrors/RePEc")`. The docstring at `:20` repeats it.
- `scripts/catalog_rel_repec_redif.py:233`: `--mirror` is `required=True`, so there is no default. The docstring at `:3,27` names `/data/mirrors/RePEc`.
- Indirect access to **ours/ISTEX**:
  - `scripts/harvest/catalog_istex.py --local` reads `$CLIMATE_FINANCE_DATA/raw/`.
  - `scripts/archive_traditions/detect_traditions_v1.py:38` defaults `CLIMATE_FINANCE_DATA` to `~/data/projets/Oeconomia-Climate-finance`.
  - On doudou, `~/data/projets/Oeconomia-Climate-finance/raw` is a symlink to `/home/haduong/data/datasets/ours/ISTEX/2025-11-27_484_articles_with_PDF_on_climate_finance`.
  - On padme, `.env:1` sets `CLIMATE_FINANCE_DATA=data` (repo-local), so the symlink path is not used there.

### Other EXEC + CONFIG sites, all outside the datasets area (listed for completeness)

- **climate-finance-het:**
  - `.githooks/post-checkout:45,46,53`: `/data/envs/venv/oeconomia` and its lock
  - `Makefile:265` `REL_SUD_RUNS ?= $(HOME)/data/projets/climate-finance-het/...`
  - `Makefile:353` `REL_VENUE_REGISTRIES ?= $(HOME)/data/projets/climate-finance-het/rel_venue_registries`
  - `config/corpus_store.yaml:420,429,450` (`/home/haduong/data/projets/climate-finance-het/rel_sud/...`)
  - `config/rel_screen.yaml:16`; `config/rel_sud_sources_status.yaml:12,284` (comments); `config/rel_venue_registries.yaml:12` (comment)
  - `scripts/harvest/corpus_migrate_citations_cache.py:30` (`/data/projets/dvc/oeconomia-climate-finance`)
  - `scripts/harvest/scout_tradition_coupling.py:38` (doc `HF_HOME=`)
  - `.dvc/config:5` `url = ssh://padme/data/projets/dvc/oeconomia-climate-finance`
  - padme `.dvc/config.local:2` `url = /data/projets/dvc/oeconomia-climate-finance`
  - doudou `.dvc/config.local:2` `dir = /home/haduong/data/projets/Oeconomia-Climate-finance/dvc-cache`
- **JETP-observer:**
  - `.dvc/config:5` `ssh://padme/data/projets/dvc/jetp-observer`
  - padme `.dvc/config.local:2,4` (`/data/projets/dvc/{oeconomia-climate-finance,jetp-observer}`)
  - doudou `.dvc/config.local:2` `dir = /home/haduong/data/projets/jetp-observer/dvc-cache`
  - `tests/test_jetp_reader_schema.py:13` (`/data/models/gguf/...`)
- **chemin-de-voix:**
  - About 30 scripts hardcode `Path.home() / "data/projets/chemin-de-voix/corpus"`, for example `scripts/fetch_from_inventory.py:35-36`, `harvest_corpus.py:79` and `clean_corpus.py:35`. The `train_*.sh` scripts use `$HOME/data/projets/...`.
  - `scripts/train_lora.py:29` `Path("/data/projets/chemin-de-voix/corpus")` and `:28` `/data/models/safetensors/...`
  - `scripts/clean_two_gpu.sh:18` (`/data/models/gguf/...`)
  - On padme, `~/data/projets/chemin-de-voix` is a symlink to `/data/projets/chemin-de-voix`.
- **padme:**
  - `tools/user/padme-llm/profiles/*.json` (`/data/models/gguf/...`)
  - `tools/clean-dev-cache.sh:3-4` (`/data/cache`)
  - `tools/verify-system-baseline.py:49-51` (`/data/cache/{uv,ruff,mypy}`)
  - `tools/report-system-status.sh:176` (`HF_HOME`)
- **arena** (padme):
  - `artifact_store.py:22-23` (`/data/arena-store`, `/data/cache/arena`)
  - `scripts/artifact-restore-proof.{py:16,sh:29}`
  - `start-arm.sh:26,37,61` and `drive.py:94` (`/data/models/gguf/...`)
- **search-works-for-zotero** (and its `~/data` clone):
  - Defaults:
    - `bench/redstate.py:1223` (`~/data/redstate`)
    - `bench/fixtures/smoke_library.py:76` (`~/data/menagerie-package`)
    - `bench/sitter_refusal.py` (`~/data/acceptance-arena`)
    - `bench/issue30_*.{py,mjs}` (`/home/haduong/data/projets/zoteus-bench/...`, `/home/haduong/data/cache/transformersjs`)
    - `bench/summarize_0120.py:246` (`/home/haduong/data/Zotero/fulltext.sqlite`)
    - `bench/pack_census.sh:21` (`$HOME/data/Zotero/storage`)
  - The rest are usage lines in docstrings.
- **polycentric_activity** (doudou):
  - `scripts/build_handbook_map.py:669` (`~/data/Zotero/zotero.sqlite`)
  - `scripts/harvest_oa_corpus.py:226` (`~/data/corpus-complexite`)
- **AEDIST-technical-report** (padme): `.env:4`, a comment only (`dvc cache dir /home/haduong/data/projets/Oeconomia-Climate-finance/dvc-cache`).

## Host-level (non-repo) configuration hits

**padme**
- `~/.profile:37` `export HF_HOME=/data/models/cache/huggingface`
- `~/.config/environment.d/70-model-caches.conf:2` `HF_HOME=/data/models/cache/huggingface`
- `~/.config/environment.d/triton.conf:1` `TRITON_CACHE_DIR=/home/haduong/.cache/triton`
- `~/.config/systemd/user/cadens-harvest.service:6` `Environment=CADENS_RAW_DIR=/data/projets/cadens/raw`
  - The timer is **disabled** and `/data/projets/cadens` is empty.
  - This conflicts with padme `cadens/.env`, which points at `/data/datasets/ours/agent-sessions/raw`.
- `~/.config/systemd/user/transcript-archive.service`: runs `transcript_archive.py` with no path. The timer is enabled; the path comes from `transcript_spool.py`.
- Other user units with non-data paths: `claude-nightbeat-supervisor.service:8` `HARNESS_DIR=%h/.idh`, `padme-open-webui.service:8` `DATA_DIR=%h/.local/share/...`
- `/etc/environment:2-5`: `LLAMA_CACHE=/data/models/cache`, `UV_CACHE_DIR`, `RUFF_CACHE_DIR` and `MYPY_CACHE_DIR` under `/data/cache`
- `/etc/fstab:7`: `/data` is a btrfs subvolume
- No crontab. No `DATASETS_DIR` or `IDH_ARCHIVE_ROOT` is set anywhere yet.
- `~/data` symlinks:
  - `~/data/onnx-cache` points to `/data/models/cache/onnx`
  - `~/data/cache/huggingface` points to `/data/models/cache/huggingface`
  - `~/data/projets/chemin-de-voix` points to `/data/projets/chemin-de-voix`

**doudou**
- `~/.bashrc:29-37`:
  - `CONDA_ENVS_PATH`, `MAMBA_ROOT_PREFIX` and `WORKON_HOME` under `/data/envs`
  - `CONDA_PKGS_DIRS`, `PIP_CACHE_DIR` and `TORCH_HOME` under `/data/cache`
  - `JUPYTER_PATH=/data/jupyter`
  - `UV_CACHE_DIR=$HOME/.local/share/uv-cache`
  - `HF_HOME=/home/haduong/data/cache/huggingface`
- `~/.bashrc:156` `export CADENS_RAW_DIR="${HOME}/data/projets/cadens/raw"`: the legacy path. `~/data/projets/cadens` exists but is empty, and this conflicts with doudou `cadens/.env`.
- `~/.config/environment.d/huggingface.conf:1` `HF_HOME=/home/haduong/data/cache/huggingface`
- `~/.config/systemd/user/cadens-harvest.service:6` `Environment=CADENS_RAW_DIR=/home/haduong/data/projets/cadens/raw`. The timer is **disabled**.
- `~/.config/systemd/user/transcript-archive.service.d/push-padme.conf:2` `ExecStartPost=-/usr/bin/rsync -a --partial --update %h/data/datasets/ours/agent-sessions/raw/doudou/ padme:/data/datasets/ours/agent-sessions/raw/doudou/`. This one line hardcodes **both** hosts' datasets paths. The timer is enabled.
- Crontab: one dated mutt reminder, with no data path. Nothing data-related in `/etc/environment` or the system units.
- Host symlinks into the datasets area:
  - `~/data/projets/Oeconomia-Climate-finance/raw` points to `~/data/datasets/ours/ISTEX/2025-11-27_484_articles_with_PDF_on_climate_finance` (used by climate-finance-het, see above)
  - `~/CNRS/missions/done/Cours/USTH M2 …/For students` points to `~/data/datasets/ours/Handbooks of environmental economics/`. This is a closed course folder, not a repo: FROZEN.
- Repo symlinks outside the datasets area:
  - `CIRED.digital/cired.digital/data` points to `/home/haduong/data/projets/cired.digital/`
  - 1,040 links in climate-finance-het and 557 in JETP-observer point into their `~/data/projets/*/dvc-cache` (DVC symlink checkout)
  - Relative links in aedist and grenier/DL_SDI stay inside the repo

## Paths that should NOT move to DATASETS_DIR

- `/data/models/**`, `HF_HOME`, `LLAMA_CACHE`, `~/data/onnx-cache`, `~/data/cache/huggingface`, and every padme-llm/arena/chemin-de-voix model path: these are model weights and caches. The comment in `70-model-caches.conf` says to keep them outside the snapshotted home.
- `/data/cache/*`, `/data/envs/*`, `/data/jupyter`, `/data/uv-cache`, and the doudou bashrc tool caches: these are rebuildable tool caches and environments.
- `/data/projets/{dvc, dvc-cache}`, the DVC remotes and `cache.dir` in climate-finance-het and JETP-observer, and the 1,597 DVC symlinks on doudou: these are project-versioned artifacts with content-addressed layouts. Moving them means DVC remote and cache surgery.
- `/data/projets/{cadens, chemin-de-voix, Oeconomia-Climate-finance, tmp}` and `~/data/projets/*` (chemin-de-voix corpus, climate-finance-het `rel_*` work dirs, zoteus-bench, jetp-observer, cired.digital, polycentric_activity): these are per-project working data, not shared datasets.
- `/data/padme-traces`: hardware and system snapshots from the padme tooling. Only DOC references exist (`padme/main-logbook.md:1182`, `gpu-swap-5070ti-memo.md:20`). The producer script was not found in any repo.
- `/data/arena-store` and `/data/cache/arena` (arena artifact store): benchmark artifacts.
- `~/data` scratch and work dirs (acceptance-arena, redstate, menagerie-package, Zotero-fresh, golden-*, generator-0719, clone-rung, zoteus-bench-pkg, `~/data/Zotero`, `~/data/corpus-complexite`): disposable bench state or a live Zotero profile.
- The legacy `CADENS_RAW_DIR=…/data/projets/cadens/raw` values in the padme and doudou units, the doudou bashrc and the doudou `.envrc` point at empty dirs. The live data is under `datasets/ours/agent-sessions`. This is a conflict to resolve, not a projets path to keep.

## Unknowns and limits

- **RePEc layout differs from the stated layout.**
  - On padme, `/data/datasets/external/RePEc` exists but is empty (0 entries). The 111 G mirror is at `/data/mirrors/RePEc`, with `RePEc_rsync.log` and `RePEc_refresh_2026-10-01.log` beside it.
  - On doudou, the mirror is at `~/data/datasets/external/RePEc` (108 G).
  - The climate-finance-het code defaults to the padme `/data/mirrors` location.
- No producer was found in code for `/data/padme-traces`. It may live in a root-owned script outside the scanned trees, which were not inspected.
- Not content-scanned:
  - non-git folders under `~/CNRS` (only the symlink pass covered them)
  - arena `repos/` and `workloads/` (only their gitignored config was read)
  - `~/data/ladder` upstream Zotero
  - doudou scratch and pytest-tmp repos
  - the RePEc `wfo` repo
- Gitignored files were read only when they matched `.env*`, `.dvc/config*`, `*.local.mk` or `config.local*` at depth ≤4. Other ignored config names would be missed.
- The EXEC counts are heuristic. They include docstring usage lines and test fixtures; the site lists above give only the load-bearing ones.
- **Writes outside the report:**
  - Scratch scan files went to `/home/haduong/.claude/jobs/d77349fe/tmp/`.
  - Two helper scripts were written to doudou `/tmp` (`reposcan_ro.sh`, `names_ro.sh`) and removed in the same SSH session.
  - No project file was modified.

## Migration size

**4 projects** have EXEC/CONFIG access to the datasets area: harness `~/.agents`, cadens, archiveCIRED (doudou only) and climate-finance-het (RePEc default plus the indirect ISTEX path). Plus host-level config. That makes about **25 sites**:

| Where | Sites |
|---|---|
| harness `transcript_spool.py` (code) | 4 |
| harness tests | 3 |
| cadens `.env` (2 per host) | 4 |
| cadens `.env.example` | 2 |
| cadens doudou `.envrc` | 1 |
| archiveCIRED | 5 |
| climate-finance-het RePEc default | 1 |
| host-level: doudou `push-padme.conf`, doudou `.bashrc:156`, both `cadens-harvest.service`, doudou ISTEX symlink | 5 |
| **Total** | **25** |
