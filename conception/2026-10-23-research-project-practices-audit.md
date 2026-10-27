# Research project practices: audit of the author's repositories

Annex to [2026-10-23-research-project-practices.md](./2026-10-23-research-project-practices.md).
Survey of 2026-10-23, read-only, from the author's local checkouts under
`~/CNRS`. Nothing was changed in the surveyed repositories.

## Method and limits

- **Sources.** Two survey agents (Sonnet, same family as the author of this
  note, so not independent) read the files; the author of this note re-checked
  the items marked (verified) below and read the ODEM design note and the
  JETP acceptance review.
- **GitHub scope.** 27 repositories under the author's account were pushed in
  2026. A project hosted under an organisation does not appear in that list:
  `CIRED/cired.digital` was found by asking, not by the listing.
- **Not on disk, so not read:** `Tracing-Kieu`, `fuzzy-corpus`,
  `aedist-technical-report`.
- **Read only at top level or by keyword:** see the per-repository column.
  About 40 other repositories under `projets/actifs` and `code` were not
  read. Local `.claude/rules` were read only in `climate-finance-het`.
- **Verified by the author of this note:** `climate-finance-het` `docs/`
  tracks 153 files; its naming rule `Author1999-TitleWords.pdf`
  (`AGENTS.md:58`); `paths.mk` exists; `aedist docs/pipeline-phases.md:9`
  ("Track the OUTCOME of each phase"); the figure allowlist in
  `climate-finance-het/.gitignore`; the ODEM definition; the JETP mapping
  table. Everything else is the agents' reading.

## Per repository

| Repository | Nature | Read | Notable |
|---|---|---|---|
| `climate-finance-het` | Corpus, analysis, 11 documents | Rules (17 files), architecture, deliverables, data location | Phases by dataflow; `paths.mk`; figure allowlist; wiki notebook; tracked `docs/` |
| `sen-causal-reading` | Reading project, origin of the wiki pattern | Earlier session | One Makefile for analysis and writing |
| `JETP-observer` | Ledger, ODEM applied | Mapping to ODEM, roadmap | O + D + descriptive E, M empty; ontology to be versioned in time |
| `aedist` | Four-phase pipeline | `docs/pipeline-phases.md` | Tracks the outcome of each phase |
| `polycentric_activity` | Several articles | Earlier session | `article-*` directories, own Makefiles |
| `cadens` | Paper plus tooling | Earlier session | `macros.tex` with a `check-no-literals` target |
| `livre-milliards-climat` | Book | Earlier session | Works directly on `main`; "no IDH, no git-erg" |
| `maiba` | Tool | AGENTS.md, Makefile, README | Config file; independent reviewer on another model; uv |
| `klem-closure-python` | Reproduction of an Excel model | README, Makefile, `JOURNAL.md` (to line 40) | Journal as notebook; oracle from cached workbook values; no uv, no lock; commits on `main` |
| `llm_benchmarks` | Measurement tool | AGENTS.md | Raw store ignored, derived summary tracked; strictest uv policy; commits on `main` |
| `corpus-access-bench` | Pre-registered evaluation | README, `.gitignore`, two tests | Immutable campaign directories; sealed instrument with hash manifest; no lock file in git |
| `archiveCIRED` | Archive index, Zotero reconciliation | AGENTS.md, Makefile, STATE.md, `.gitignore` | File-target Makefile; network targets outside `make check`; tracked `outputs/` as review handoff |
| `cired.digital` (RAG) | Chatbot and usage analysis | README, Makefile, `.gitignore`, tree | Byte-comparison regression; writing-side `slides` target; parent directory for confidential management |
| `ThinkTanksSurveyor`, `VN-Power-Scenario` | Older repositories | Earlier session | Aligned to uv; `VN-Power-Scenario` left alone by the author's decision |

## Deviations, triaged

Triage is the author of this note's proposal. The author decides which class
each belongs to.

### To align soon

- **`corpus-access-bench`: no `pyproject.toml` and no lock file in git.** The
  repository is deposited on Zenodo, so a lock is part of what a reuser needs.
  Not among the four repositories already ticketed for the uv migration.
- **`klem-closure-python`: `venv` and `pip`, no lock.** Contradicts the uv
  rule (`rules/coding-python.md`). Also not among the ticketed four.

### To align when convenient

- **`rules/zotero.md` is too coarse for `docs/`.** Proposal: ignore the PDFs,
  track notes and design documents. This is a change to a rule, so it needs
  its own branch and an other-family review seat.
- **`climate-finance-het` says "Phase 1 to 4"** in its rules, against the
  plain-language naming rule. Low risk.
- **`klem-closure-python` and `llm_benchmarks` commit on `main`.** Small
  repositories with few commits (13 and 2); alignment would add PR overhead
  for little gain, so decide per repository.
- **`llm_benchmarks`: `.gitignore` lists `.venv/`** while its own rules say no
  `.venv` may exist. Cosmetic.
- **`cired.digital`: no `AGENTS.md` or `CLAUDE.md`** at the root of the code
  repository (only README, `docs/CODE_STYLE.md`, `CONTRIBUTING.md`).
- **`archiveCIRED`: a stale comment in `.gitignore`** ("Generated outputs, not
  handoff artifacts") while `outputs/` is tracked as the review handoff.

### To check

- **`cired.digital` tracks an anonymised log archive**
  (`reports/monitor-logs-anon_20260210.zip`, 6.8 MB). Whether its content is
  fit for an open repository was not checked; the archive was not opened.
- **`JETP-observer`: ontology versioning in time.** Its own review asks for
  it; whether it is done was not checked.

### Justified idiosyncrasies

- `docs/` tracked for notes in `climate-finance-het`, `aedist`,
  `JETP-observer` (feeds the rule proposal above).
- A single Makefile in `sen-causal-reading` and `cired.digital`, the boundary
  with the writing side being stated in a comment.
- `livre-milliards-climat` on `main`: prose, which the harness already
  exempts.
- `llm_benchmarks`: raw store ignored, derived summary tracked.
- `corpus-access-bench` without a Makefile: parameterised scripts and tests.
- `maiba` without `docs/`: design in `ARCHITECTURE.md`.

### Live with it

- Inconsistent document file names: `Author1999-TitleWords.pdf`
  (`climate-finance-het`), `Hoover-2001-...` (`sen-causal-reading`),
  `Cinelli_Forney_Pearl_2024_...` (Gavard), one duplicated name
  `AbrishamiKnappe2025-AbrishamiKnappe2025.pdf` (`polycentric_activity`). The
  author's decision: alignment is optional.

## Not in this note

- The pending move of two sections of `rules/coding-python.md`
  (bibliography paragraph, "Build (Make)") to other rule files. Separate
  change, awaiting the author's choice of destination.
- Any new rule. This note and its annex are reference material.
