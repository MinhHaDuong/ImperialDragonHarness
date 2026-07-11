# AEDIST Technical Report - Project Memory

## Key insights
<!-- /dream consolidation 2026-06-16 -->

- Anchor on stable identifiers, never on position: label-keyed test extraction, grep-relocation over line hints, slug-keyed memories — every positional anchor (line numbers, section titles, annex letters) broke at least once during the 2026-06 manuscript waves.
- In multi-session and background work, cwd and branch state are not yours: parallel sessions legitimately move a worktree's branch; sync to origin before any fan-out, anchor every mutating command in one compound (`cd X && …` / `git -C`), and verify with `rev-parse`. Forge automation is also not idempotent — check forge state before retrying a merge.
- Agent-surveyed numbers are hypotheses; committed artifacts are the source of truth — re-derive before writing prose, and guard quoted literals with re-derivation tests.
- The ticket/state dependency graph is the only durable "remember later" primitive: reminders → an OPEN ticket `Blocked-by` the trigger (auto-fires in `erg ready` when it closes); handoffs → STATE + edges; closed tickets and orphaned worktree WIP silently lose their unlanded content (re-ticket it, never leave it in a closed ticket's notes).
- Dissemination is not the paper — code+data need their own persistent citable DOI (a mutable forge URL is not one), and register precision matters ("article" = peer-reviewed only; negative prose guards beat positive wording pins — the polarity rule).

## Project Structure
- **Monorepo**: code absorbed into report repo (2026-04-02). aedist GitHub archived.
- **Report dir**: `/home/haduong/CNRS/papiers/actif/AEDIST-technical-report/`
- LaTeX built with **Tectonic** (XeTeX engine): `tectonic report.tex`
- Python managed with **uv** (no venv): `uv run --project ...`
- `UV_CACHE_DIR=/scratch/uv` (set in Makefile)

## Pipeline
- Manager+worker dispatch via `make` targets in `experiments/Makefile`
- `experiments/models.yaml` — 46 model registry
- `experiments/experiments.toml` — routers, model sets, and condition configs
- `experiments/outputs/` — tracked in git (census, rag, multiturn, web, frontier, decomposed, sourced)
- `make tables` → generates LaTeX in `report/inputs/generated/`
- `make` or `make all` → builds `report.pdf`

## Design Decisions
- Tables generated **per-table** not per-experiment (tables combine data from multiple experiments)
- `inputs/generated/*` gitignored; `experiments/outputs/` tracked

## Reference repos
- [Homepage publication list](reference_homepage_publication_list.md) — `~/CNRS/html` BibLaTeX→HTML generator (git root = src/, no remote/direct-master, `rtk proxy pytest`, 6-type relation model, make tidy-bib/validate/inspect)

## User Preferences
- [Linux only](user_platform.md) — omit macOS/Windows instructions
- Wants minimal, non-over-engineered solutions
- French-language report about Vietnamese thermal power plants as AI benchmark task

## Active
- [Release needs code+data DOI](project_release_needs_codedata_doi.md) — disseminating the paper isn't disseminating the work; persistent DOI for code+data (Zenodo concept 10.5281/zenodo.20715179) is a release exit criterion, not a GitHub URL
- [Durable reminder = blocked open ticket](feedback_durable_reminder_is_blocked_open_ticket.md) — "remember in N months" goes in an OPEN ticket Blocked-by the trigger (auto-surfaces in erg ready), never a closed-ticket note
- ["Article" = peer-reviewed only](feedback_no_article_for_working_paper.md) — never call a working paper/preprint an "article" (EN or FR); use working paper/preprint/report/étude/document de travail
- [Ruff hook reports, not deletes](feedback_ruff_hook_reports_not_deletes.md) — global lint-on-edit hook now exempts F401/I001/UP from autofix; import-in-same-Edit rule is hygiene not trap-avoidance; AEDIST workflow.md § ruff is stale
- [Orphaned WIP = unlanded exit-criteria](feedback_orphaned_wip_is_unlanded_exit_criteria.md) — uncommitted WIP in a stale worktree may be a closed ticket's dropped deliverable; preserve, verify it runs, re-ticket (0609→0673)
- [Side book — *Idées reçues* / finance climat](project_book_idees_recues_finance_climat.md) — separate repo; Le Cavalier Bleu dossier ready to send via Romain Blachier
- [Editorial / trade-book working style](feedback_editorial_book_work.md) — multi-agent sims welcomed; grand-public legibility; no namedrop/family in pitch files
- [Reference v1 defects & pipeline](project_reference_fix1.md) — v1 scores as-is, defects documented (PROVENANCE checklist); fix1 leapfrogged, never shipped; corrections via pipe 0420→0416→0419, adoption 0413 after 0412; fix the master + regenerate, never patch downstream
- [No invented names](feedback_no_invented_names.md) — reference names must be source-attested; disambiguate structurally (status/units), never synthesize a name
- [Verbatim by construction](feedback_verbatim_by_construction.md) — line-shaped edits via grep/sed/awk + count guards, not csv round-trips; diff-vs-source is the provenance evidence
- [Three-quality argument](project_three_quality_argument.md) — paper's spine: data / answer / method, four limits split 2/2, method quality is perpendicular not a fifth limit (ticket chain 0145–0154)
- [Coherence axis decomposition](project_coherence_axis_decomposition.md) — Coherence dimension → internal/external reference-free composites, per-row pass/fail; + `level` enum dimension (granularity, capacity plausibility is level-conditional); ticket chain 0201→0396→0397, 0401→0402
- [Econom'IA 2026](project_economia_2026.md) — talk delivered & archived: tag economia-2026-cergy (bbc4a013), HAL hal-05644906, release with presented PDF; technical report diffused 2026-06-15: tag economia-2026-report (2da83d04), 65pp widow-free; deposited on HAL 2026-06-16 as working paper hal-05658462 (type UNDEFINED, CC-BY, seeAlso→talk; arXiv deferred to v2)
- [Exp 1 module scheme](project_exp1_module_scheme.md) — modules renamed 1-6/A-D; Exp 1 baseline = 2_goal+5_table
- [Exp 1 design decisions](project_exp1_design_decisions.md) — URL unguarded (intentional), >30MW in both files, Notes column; pending: harness.py + README + Annex A (ticket 0175)
- [Reproducible pipeline](feedback_reproducible_pipeline.md) — test harness must be clear and reproducible
- [Make not loops](feedback_make_not_loops.md) — Makefile dependencies, not shell loops
- [Local vs cloud](feedback_local_vs_cloud.md) — always pair local + frontier through all sweeps
- [Pipeline UX](feedback_pipeline_ux.md) — progress bars, circuit breakers, checkpointing
- [Fast pipelines](feedback_fast_pipelines.md) — batch ops on local data must feel instant
- [Review before merge](feedback_review_before_merge.md) — wait for review agents before merging
- [gh merge in worktree](feedback_gh_merge_worktree.md) — pass `--repo` flag to avoid worktree conflict
- [nohup PATH on padme](feedback_nohup_path.md) — always export ~/.local/bin before nohup
- [PDF converter architecture](project_pdf_converters.md) — 3 shipped, 2 ticketed (#81-#85)
- Padme: A4000 16GB + 3060 12GB + 128GB RAM, Ollama 0.20.0, project dir `~/aedist-technical-report/`
- [CNRS Emmy](reference_emmy.md) — CNRS-hosted Mistral instance, potential third inference tier
- OPENROUTER_API_KEY in .env (renewed 2026-04-02)
- [evaluate-all overwrites](feedback_evaluate_all_overwrite.md) — run sweeps to separate dirs then merge (#92)
- [RAG results](project_sweep2_results.md) — Mistral Small 4 beats GPT-5.4 with RAG, $0.89 total
- API key: `~/.claude/.env` has ANTHROPIC_API_KEY, repo `.env` has OPENROUTER_API_KEY
- [Autonomous Claude on Padme](reference_autonomous_padme.md) — nohup recipe for ticket-driven autonomous work
- [Interactive Claude on Padme via tmux](reference_tmux_padme.md) — named tmux session recipe (claude1, claude2, …) for live driving
- [Worktrees not stash](feedback_worktree_not_stash.md) — use git worktree for cross-branch work, never stash+checkout
- [evaluate-all record quality](feedback_evaluate_all_quality.md) — spot-check for absolute paths and -runN in model names
- [Ollama num_ctx](feedback_ollama_num_ctx.md) — /v1/ ignores num_ctx, must use native /api/chat
- [Model registry consolidation](project_model_registry_consolidation.md) — single models.yaml + experiments.toml
- [Shared utils](feedback_shared_utils.md) — reusable helpers go in util.py with comprehensive tests
- [Pipe table splitting](feedback_pipe_table_splitting.md) — split multi-table responses, score each independently
- [Multiturn all turns](feedback_multiturn_all_turns.md) — join all assistant turns, last turn may be truncated
- [Autonomous = execute](feedback_autonomous_means_execute.md) — "while I'm away" means kick off the skill, not write a plan-for-approval
- [No typo callouts](feedback_no_typo_callouts.md) — never reference user typos in tickets, commits, or any durable artefact
- [No ps -ef](feedback_no_ps_ef_in_claude.md) — process listings with cmd-line args leak API keys via Claude Code's bash wrapper
- [Check sister files first](feedback_check_sister_files_first.md) — before writing integration code, read an existing sibling that already solves the same problem
- [Display-name sweep hits plot scripts](feedback_display_name_sweep_includes_plot_scripts.md) — stale model-name fix in prose must sweep `plot_*.py` label maps too (they render into manuscript figures); disambiguate vs genuinely-different registry entries before fixing
- [Local 9B near ceiling](project_local_9b_near_ceiling.md) — qwen3.5:9b at F1=0.984 on direct (n=1); may collapse priority-3 scope if reproduces
- [Pydantic unknown kwargs](feedback_pydantic_unknown_kwargs.md) — test schema *projection effects* (asymmetric values), not literal construction; BaseModel accepts unknown kwargs silently
- [STRUCTURED_DIRS registry](project_structured_dirs_registry.md) — Makefile has hardcoded sweep-dir list; new outputs must be registered or extract skips them
- [Ticket housekeeping via PR](feedback_ticket_housekeeping_on_main.md) — ALL main-targeted commits (tickets, STATE) go through branch+PR; GH006 branch protection rejects direct pushes; merge with `--merge --auto`, never squash
- [gaze fork dies in bg jobs](feedback_gaze_fork_dies_in_background_jobs.md) — in background sessions run sonnet reviewers + /verify-gate directly; /gaze's forked reviewers evaporate
- [Teams worklist purges completed](feedback_teams_worklist_purges_completed.md) — shared worklist is real but completed tasks vanish; collect results from agent return values, pre-tier model per batch, smoke-test one first
- [Verify against synced main](feedback_verify_against_synced_main.md) — sync local checkout to origin before any verification/review fan-out; a stale tree yields false FAILs on already-merged fixes
- [Shell timeout, no loops](feedback_shell_timeout_no_loops.md) — shells stall on gh/git/CI calls; wrap every network call in `timeout`, never write shell poll-loops; queue native auto-merge and check back later
- [Teams raid region bundling](feedback_teams_raid_region_bundling.md) — large prose-edit wave via Teams: sweeps-first, bundle tickets by manuscript region (one PR/section), emitters merge free, invasive PR last, red-team at end
- [Render & adjust tables](feedback_render_and_adjust_tables.md) — after ANY table change, always render the PDF and check/adjust column widths of ALL tables (overfull \hbox); never assume fit
- [No caveats in captions](feedback_no_caveats_in_captions.md) — captions state plainly what the figure/table shows; caveats, hedges, method qualifications go in body/annex, never the caption
- [Pagination widow verification](feedback_pagination_widow_verification.md) — fix widows by shaving signposts/roadmaps/recaps first; verify by rendering the exact page to PNG and Reading it (not pdftotext grep); cross-PR layouts interact
- [haiku truncated final reports](feedback_haiku_truncated_final_reports.md) — haiku agents end turn on narration instead of long structured reports; run mechanical checks inline or demand one-line verdicts
- [rtk git log stale](feedback_rtk_git_log_stale.md) — rtk-filtered `git log` hides/lags merge commits; use `rtk proxy git` for ground truth on git state
- [Build from user worktree](feedback_build_from_user_worktree.md) — user edits main tree while you're in a worktree → same file diverges; build from their source, verify before `checkout --`
- [Live-edit build watcher](feedback_live_edit_build_watcher.md) — for rapid editing passes, run a background watcher that rebuilds on save and exits-on-failure to re-invoke you; silent on clean builds
- [Clean-room force-rebuild test](feedback_cleanroom_force_rebuild_test.md) — `make -B -n` not `make -n` is the structural cleanroom test; plain `-n` passes spuriously when artifacts are timestamp-fresh
- [Stale line numbers across waves](feedback_stale_line_numbers_across_waves.md) — feasibility line hints die after each merged wave; later executors re-locate by label/grep
- [Use quickpr for chores](feedback_use_quickpr_for_chores.md) — one-shot chore PRs (tickets/docs/.claude/workflows/*.md) go through `scripts/quickpr.sh`, not the 7-command manual ceremony
- [erg ID collision](feedback_erg_id_collision.md) — branch-allocated ticket IDs can be re-allocated on main in parallel; land ticket files fast, erg check after every rebase
- [Merge review merge cadence](feedback_merge_review_merge_cadence.md) — merge each PR as soon as approved+green; no long-lived branches, no batch merges
- [Handoff in STATE not tickets](feedback_handoff_in_state_not_tickets.md) — handoffs go in STATE.md + MASTERPLAN + Blocked-by edges, never a tracker ticket
- [~/.claude = IDH checkout](reference_claude_dir_is_idh.md) — the live harness dir is the ImperialDragonHarness clone on doudou; PR then `git -C ~/.claude pull`
- [Stacked PR waves](feedback_stacked_pr_waves.md) — same-file raid waves go out stacked (base = previous wave's branch); rebase the stack at every gate, the author lands decisions mid-raid
- [BG merge anchoring + auto-merge race](feedback_bg_merge_anchoring.md) — erg-pr-merge in bg sessions: anchor `cd <pr-worktree> && …` in one compound; check PR state before any retry (bounced run may have queued auto-merge)
- [pgrep self-match watcher](feedback_pgrep_self_match_watcher.md) — watcher loops that `pgrep -f` their own pattern self-match and never exit; gate on a captured PID + timeout fallback
