# Project Memory

## Key insights
- The repo is a **4-paper research programme** (`climate-finance-het`); the Œconomia R&R is the active deadline track, run as a version ladder (v2.0.3 → v2.0.5) gated by tracker tickets. Submission records live outside the repo under `papiers/<state>/<track>/`.
- **Methodological honesty is a hard norm**: computation *corroborates* history (don't oversell breaks / claim "Paris didn't matter"); cite only pipeline numbers traceable to an archived output.
- **Heavy worktree + parallel-session discipline**: shared uv env on /data, data on-demand, never rebase with dirty DVC symlinks, branch-before-edit, check the filesystem before asserting work undone.
- The author optimizes for **diamond-OA integrity over prestige** (no APC, CNRS Section 41), an HET academic register (not motivational), and weekends off.
- **Two-machine flow** (doudou ↔ padme): data flows padme→doudou only; uv isn't in non-interactive PATH; phase separation (a manuscript build never triggers Phase 1).

## ⚠️ Read first — project relocated/renamed 2026-06-19
- [Reorg 0159 relocation](project_reorg_0159_relocation.md) — engine now `~/CNRS/projets/actifs/climate-finance-het/` (GitHub `climate-finance-het`); records in `papiers/<state>/<track>/`; older memories referencing the old path/name are stale. Follow-up: ticket 0160.

## Corpus terminology
- Full corpus: "scholarship around climate finance" (not "climate finance scholarship" — too narrow)
- Core subset (cited_by_count >= 50): the influential works

## Naming quirk
- SciSpace scripts/files used "scispsace" (typo in CSV source column); fixed in #452 — catalog_merge now derives source name from filename

## Three-act periodization (history, corpus-corroborated)
- I. Before climate finance (1990–2006)
- II. Crystallization (2007–2014) — breaks at 2007 (cosine) and 2013 (JS)
- III. Established field (2015–2025) — only a marginal JS rise at Paris 2015, no rupture
- Framing: history-first, corpus *corroborates* (detection blind to COP calendar). Don't say "endogenous / not imposed from COP". See [[feedback_oversell_breaks]].

## Oeconomia figure design decisions
- User rejected z-score plot as "too technical for HPS audience"
- User rejected hand-curated Table 1: "I want code. Clustering to DETECT."
- User rejected inset legend swatches as "failed idea"

## User context
- [user_cnrs_section41.md](user_cnrs_section41.md) — CNRS Section 41 researcher; publications optimized for peer-reviewed credibility in HPS/STS, not prestige/IF
- [user_orcid.md](user_orcid.md) — ORCID: 0000-0001-9988-2100 (never guess)

## Workflow preferences
- **Be autonomous for all search** — do not stop to ask, just proceed
- **Use worktrees** for feature branches
- **Create PRs** for each ticket — user wants to review via GitHub PRs
- User runs parallel sessions — don't assume data files are stale

## Agent identity
- [reference_agent_identity.md](reference_agent_identity.md) — HDMX-coding-agent is a git-author alias only; all GH actions appear as MinhHaDuong; use `--comment` not `--approve` for self-review

## Remote machine: padme
- Repo at `~/Climate_finance` (NOT under ~/CNRS/)
- Ollama often running (~19GB RSS) — budget memory accordingly
- `uv` at `~/.local/bin/uv` (not in default PATH for non-interactive ssh)
- Use `nohup` for long-running tasks; logs in `/tmp/`
- GPUs: NVIDIA A4000 (16GB) + RTX 3060 (12GB)
- torch via uv extras: `--extra cpu` (doudou) or `--extra cu130` (padme, CUDA 13.0)
- Cache config in `/etc/environment` (UV_CACHE_DIR, RUFF, MYPY → `/data/cache/`); pytest in `/etc/profile.d/dev-cache.sh`
- Non-interactive SSH doesn't source `/etc/profile.d/` — use `/etc/environment` for env vars that must always apply

## DOIfetch sync procedure
- See [project_doifetch_sync.md](project_doifetch_sync.md) for full details

## DVC integration
- See [project_dvc_integration.md](project_dvc_integration.md) for full details

## OpenRouter / LLM
- API key in `~/.bashrc` (OPENROUTER_API_KEY)
- Background bash tasks don't inherit `~/.bashrc` — must export key explicitly
- Prompt must request flat JSON keys (not numbered) — LLMs default to numbered

## OpenAlex
- Premium API key ($2/day) in `.env` (loaded via python-dotenv)
- S2 API key available (in docs/), rate-limited to 1 req/s even with key
- JETP query disabled (ambiguous acronym, 72K hits mostly physics journal noise)

## Performance notes
- Never use `iterrows()` on 20K+ DataFrames — vectorize with pandas masks

## Toolchain
- [project_uv_path_fix.md](project_uv_path_fix.md) — `$(UV_RUN)` + PATH export in Makefile (#719); follow-on 0088 for release templates
- [project_worktree_env_data.md](project_worktree_env_data.md) — worktrees: shared uv env on /data (#797), data on-demand via `make data` (#801), absolute core.hooksPath gotcha; tickets 0145/0157

## Technical report
- [project_techrep_rewrite.md](project_techrep_rewrite.md) — structural rewrite plan: reproducibility note framing, two-part structure, variable geometry
- [project_techrep_split.md](project_techrep_split.md) — split into corpus-report.qmd + analysis-only technical-report.qmd (2026-04-14)

## Break detection
- [feedback_oversell_breaks.md](feedback_oversell_breaks.md) — mid-2010s JS divergence is real; don't claim "Paris didn't matter"; computation corroborates history

## Imperial Dragon harness
- [project_imperial_dragon.md](project_imperial_dragon.md) — Dragon Dreaming → Imperial Dragon (5 claws); generic harness at ~/.claude/ backed by ImperialDragonHarness repo; PR #628

## Telemetry & instrumentation
- [reference_stats_cache.md](reference_stats_cache.md) — ~/.claude/stats-cache.json: free daily usage checkpoint for all surfaces
- [reference_agentic_harness.md](reference_agentic_harness.md) — superseded by ImperialDragonHarness; old ~/.agent/ clone still has history

## Oeconomia R&R
- [project_oeconomia_rr_pipeline.md](project_oeconomia_rr_pipeline.md) — major R&R (2026-05-24); version ladder v2.0.1–v2.0.5 gated by tracker tickets; PR #800
- [project_rr_traceability_ledger.md](project_rr_traceability_ledger.md) — 60-remark response ledger path + author rule: no non-actionable close, HITL sign-off per row
- [feedback_version_increment_planning.md](feedback_version_increment_planning.md) — plan as version increments, ratchet-first, not waterfall; I draft decision options

## Journal strategy
- [project_journal_strategy.md](project_journal_strategy.md) — data paper → RDJ4HSS (diamond OA), methods paper deferred (QSS/Cultural Analytics/JEM shortlist)
- [reference_rdj4hss.md](reference_rdj4hss.md) — RDJ4HSS format specs (2,500 words, sections, citation style) derived from published exemplar
- [project_gide_conference.md](project_gide_conference.md) — Charles Gide conference (Vannes, 2026-07-02–07); RHPE call for papers (Classiques Garnier), ~7p HET paper

## Parked ideas (post-submission)
- `docs/braindump-2026-03-18.md` in repo — repro packages, Makefile modularization, skill-based agent coordination, local issue tracking, conversation replay
- [project_ollama_experiment.md](project_ollama_experiment.md) — benchmarking local LLMs (Ollama on Padme) on the project harness overnight

## OPIDoR
- [reference_opidor.md](reference_opidor.md) — DMP import: use RDA/maDMP JSON format, select "RDA" in format picker; UI switches to English after import

## Publications list
- [reference_publist.md](reference_publist.md) — ~/CNRS/html/src/Ha-Duong.bib → make → index.html; @article only for accepted papers

## Quarto
- [feedback_quarto_var_vs_meta.md](feedback_quarto_var_vs_meta.md) — `{{< var >}}` only reads `_variables.yml`; use `{{< meta >}}` with `metadata-files:` instead
- [reference_trackchange_review_workflow.md](reference_trackchange_review_workflow.md) — marked-PDF review loop: `\rradd` blue track-change macro + per-doc render; accept = strip to clean source

## Feedback
- [feedback_erg_close_archive.md](feedback_erg_close_archive.md) — PROVISIONAL (pending erg close step-4 auto-archive): `erg close` and `erg archive` are separate; run both when closing pre-PR or /gaze flags the unarchived ticket (burned a round on 0149)
- [feedback_enterworktree_stuck_cwd.md](feedback_enterworktree_stuck_cwd.md) — EnterWorktree/cwd-skills target the wrong repo when session base cwd is parked off-project; fall back to manual `git worktree add` + `git -C`
- [feedback_het_register.md](feedback_het_register.md) — manuscript prose = HET academic register, not American motivational/business-book cadence (no "cash out", "this is what X is", punchy beats)
- [feedback_yaml_quoting.md](feedback_yaml_quoting.md) — use `'"phrase"'` not `"phrase"` in corpus_collect.yaml for phrase search queries
- [feedback_no_long_running.md](feedback_no_long_running.md) — don't launch long-running tasks (make, rendering); let user run in their terminal
- [feedback_phase_separation.md](feedback_phase_separation.md) — make manuscript must never trigger Phase 1 scripts or API calls
- [feedback_data_direction.md](feedback_data_direction.md) — data flows padme→doudou only; never push data from doudou to padme
- [feedback_no_heavy_deps.md](feedback_no_heavy_deps.md) — don't add heavy deps (jupyter) when a simple approach (YAML, hardcode) works
- [feedback_review_agent_worktree.md](feedback_review_agent_worktree.md) — review agents must read from PR branch worktree, not main
- [feedback_overnight_exploration.md](feedback_overnight_exploration.md) — overnight sessions must prioritize deliverables (next paper), not just code tooling; use runbooks/overnight-exploration.md
- [feedback_no_apc.md](feedback_no_apc.md) — APCs are scams; choose diamond OA venues (integrity, excellence, care)
- [feedback_parallel_work.md](feedback_parallel_work.md) — user works in VSCode terminal in parallel; check filesystem before asserting something hasn't been done
- [feedback_no_amend_pr.md](feedback_no_amend_pr.md) — don't amend commits on open PRs; force push makes GitHub diffs confusing
- [feedback_no_md_in_md.md](feedback_no_md_in_md.md) — never put markdown (## headings) inside fenced blocks; extract to a real file
- [feedback_worktree_search.md](feedback_worktree_search.md) — scan parent dirs and /tmp for stale worktree directories, not just `git worktree list`
- [feedback_no_noverify.md](feedback_no_noverify.md) — never bypass pre-commit hooks with --no-verify; always branch first
- [feedback_worktree_local_hook_commit.md](feedback_worktree_local_hook_commit.md) — commit a branch's own hook fix via `git -c core.hooksPath=<worktree>/hooks` when hooksPath is absolute
- [feedback_branch_before_edit.md](feedback_branch_before_edit.md) — always checkout target branch before editing files; never edit on main then move
- [feedback_onstart_trigger.md](feedback_onstart_trigger.md) — on-start runbook must execute automatically before first response, not wait to be asked
- [feedback_harness_not_here.md](feedback_harness_not_here.md) — harness now at ~/.claude/ (Imperial Dragon); project .claude/ has project-specific residuals only
- [feedback_make_corpus.md](feedback_make_corpus.md) — never suggest bare `dvc repro`; always use `make corpus` (padme) or `make corpus-sync` (doudou)
- [feedback_no_rebase_dvc.md](feedback_no_rebase_dvc.md) — never rebase when DVC symlinks are dirty; use merge + stash/pop
- [feedback_simplest_fix.md](feedback_simplest_fix.md) — don't add hooks/exceptions; restructure the operation to work within existing rules (e.g. ff merge vs --no-ff)
- [feedback_ssh_padme.md](feedback_ssh_padme.md) — can SSH from doudou to padme; don't say "I can't reach padme"
- [feedback_ssh_padme_path.md](feedback_ssh_padme_path.md) — always prepend PATH=$HOME/.local/bin for padme SSH (uv not in non-interactive PATH)
- [feedback_weekend_boundary.md](feedback_weekend_boundary.md) — no project work on weekends; mental health is non-negotiable
- [feedback_verify_before_advising.md](feedback_verify_before_advising.md) — always WebFetch conference/journal URLs before offering strategic advice
- [feedback_dropna_before_merge.md](feedback_dropna_before_merge.md) — always dropna before merge/set_index on DOI; pandas NaN==NaN causes cartesian explosion
- [feedback_grep_before_commit.md](feedback_grep_before_commit.md) — grep whole project before committing pattern fixes; don't rely on reading individual files
- [feedback_inspect_ref_readonly.md](feedback_inspect_ref_readonly.md) — inspect another ref with git grep/show, never git checkout (detaches HEAD, clobbers a parallel session's branch)
- [feedback_oversell_breaks.md](feedback_oversell_breaks.md) — mid-2010s JS divergence is real; computation corroborates history, not the reverse
- [feedback_tectonic_next.md](feedback_tectonic_next.md) — next project: Tectonic + plain LaTeX, not Quarto (incremental builds)
- [feedback_verify_deferral_tracker.md](feedback_verify_deferral_tracker.md) — verify deferral tracker still open + in-scope before closing; rehome if orphaned
- [feedback_no_tool_for_single_use.md](feedback_no_tool_for_single_use.md) — single-use op → run the command, don't build a tested reusable tool (scrapped #804)
- [feedback_file_decisions_with_submission.md](feedback_file_decisions_with_submission.md) — file journal decisions/referee reports as tracked text beside their submission folder; verify extraction before deleting source
- [feedback_manuscript_number_provenance.md](feedback_manuscript_number_provenance.md) — cite only pipeline numbers that trace to an archived output; v1-pinned manuscript can silently drift from live-pipeline stats (the 0.68 case)
