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
- [Homepage publication list](reference_homepage_publication_list.md)

## User Preferences
- [Linux only](user_platform.md)
- Wants minimal, non-over-engineered solutions
- French-language report about Vietnamese thermal power plants as AI benchmark task

## Active
- [Release needs code+data DOI](project_release_needs_codedata_doi.md)
- [Durable reminder = blocked open ticket](feedback_durable_reminder_is_blocked_open_ticket.md)
- ["Article" = peer-reviewed only](feedback_no_article_for_working_paper.md)
- [Ruff hook reports, not deletes](feedback_ruff_hook_reports_not_deletes.md)
- [Orphaned WIP = unlanded exit-criteria](feedback_orphaned_wip_is_unlanded_exit_criteria.md)
- [Side book — *Idées reçues* / finance climat](project_book_idees_recues_finance_climat.md)
- [Editorial / trade-book working style](feedback_editorial_book_work.md)
- [Reference v1 defects & pipeline](project_reference_fix1.md)
- [No invented names](feedback_no_invented_names.md)
- [Verbatim by construction](feedback_verbatim_by_construction.md)
- [Three-quality argument](project_three_quality_argument.md)
- [Coherence axis decomposition](project_coherence_axis_decomposition.md)
- [Econom'IA 2026](project_economia_2026.md)
- [Exp 1 module scheme](project_exp1_module_scheme.md)
- [Exp 1 design decisions](project_exp1_design_decisions.md)
- [Reproducible pipeline](feedback_reproducible_pipeline.md)
- [Make not loops](feedback_make_not_loops.md)
- [Local vs cloud](feedback_local_vs_cloud.md)
- [Pipeline UX](feedback_pipeline_ux.md)
- [Fast pipelines](feedback_fast_pipelines.md)
- [Review before merge](feedback_review_before_merge.md)
- [gh merge in worktree](feedback_gh_merge_worktree.md)
- [nohup PATH on padme](feedback_nohup_path.md)
- [PDF converter architecture](project_pdf_converters.md)
- Padme: A4000 16GB + 3060 12GB + 128GB RAM, Ollama 0.20.0, project dir `~/aedist-technical-report/`
- [CNRS Emmy](reference_emmy.md)
- Repo `.env` holds no secret values since PR #1165 (2026-07-14, ticket 0679): it is only a `KEYS=` manifest naming which central secrets to pull (e.g. `github:AGENT_GH_TOKEN`, `openrouter:OPENROUTER_API_KEY_AEDIST=OPENROUTER_API_KEY`); safe to read and edit directly
- [evaluate-all overwrites](feedback_evaluate_all_overwrite.md)
- [RAG results](project_sweep2_results.md)
- API keys live centrally in `~/.claude/.env` (ANTHROPIC_API_KEY, OPENROUTER_API_KEY_AEDIST, …); the repo `.env` only names them via `KEYS=`
- [Autonomous Claude on Padme](reference_autonomous_padme.md)
- [Interactive Claude on Padme via tmux](reference_tmux_padme.md)
- [Worktrees not stash](feedback_worktree_not_stash.md)
- [evaluate-all record quality](feedback_evaluate_all_quality.md)
- [Ollama num_ctx](feedback_ollama_num_ctx.md)
- [Model registry consolidation](project_model_registry_consolidation.md)
- [Shared utils](feedback_shared_utils.md)
- [Pipe table splitting](feedback_pipe_table_splitting.md)
- [Multiturn all turns](feedback_multiturn_all_turns.md)
- [Autonomous = execute](feedback_autonomous_means_execute.md)
- [No typo callouts](feedback_no_typo_callouts.md)
- [No ps -ef](feedback_no_ps_ef_in_claude.md)
- [Check sister files first](feedback_check_sister_files_first.md)
- [Display-name sweep hits plot scripts](feedback_display_name_sweep_includes_plot_scripts.md)
- [Local 9B near ceiling](project_local_9b_near_ceiling.md)
- [Pydantic unknown kwargs](feedback_pydantic_unknown_kwargs.md)
- [STRUCTURED_DIRS registry](project_structured_dirs_registry.md)
- [Ticket housekeeping via PR](feedback_ticket_housekeeping_on_main.md)
- [gaze fork dies in bg jobs](feedback_gaze_fork_dies_in_background_jobs.md)
- [Teams worklist purges completed](feedback_teams_worklist_purges_completed.md)
- [Verify against synced main](feedback_verify_against_synced_main.md)
- [Shell timeout, no loops](feedback_shell_timeout_no_loops.md)
- [Teams raid region bundling](feedback_teams_raid_region_bundling.md)
- [Render & adjust tables](feedback_render_and_adjust_tables.md)
- [No caveats in captions](feedback_no_caveats_in_captions.md)
- [Pagination widow verification](feedback_pagination_widow_verification.md)
- [haiku truncated final reports](feedback_haiku_truncated_final_reports.md)
- [rtk git log stale](feedback_rtk_git_log_stale.md)
- [Build from user worktree](feedback_build_from_user_worktree.md)
- [Live-edit build watcher](feedback_live_edit_build_watcher.md)
- [Clean-room force-rebuild test](feedback_cleanroom_force_rebuild_test.md)
- [Stale line numbers across waves](feedback_stale_line_numbers_across_waves.md)
- [Use quickpr for chores](feedback_use_quickpr_for_chores.md)
- [erg ID collision](feedback_erg_id_collision.md)
- [Merge review merge cadence](feedback_merge_review_merge_cadence.md)
- [Handoff in STATE not tickets](feedback_handoff_in_state_not_tickets.md)
- [~/.claude = IDH checkout](reference_claude_dir_is_idh.md)
- [Stacked PR waves](feedback_stacked_pr_waves.md)
- [BG merge anchoring + auto-merge race](feedback_bg_merge_anchoring.md)
- [pgrep self-match watcher](feedback_pgrep_self_match_watcher.md)
