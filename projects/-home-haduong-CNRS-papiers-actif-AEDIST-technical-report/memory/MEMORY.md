# AEDIST Technical Report - Project Memory

## Key insights
<!-- /dream consolidation 2026-06-12 -->

- Anchor on stable identifiers, never on position: label-keyed test extraction, grep-relocation over line hints, slug-keyed memories — every positional anchor (line numbers, section titles, annex letters) broke at least once during the 2026-06 manuscript waves.
- In multi-session and background work, cwd and branch state are not yours: parallel sessions legitimately move a worktree's branch; anchor every mutating command in one compound (`cd X && …` / `git -C`) and verify with `rev-parse` before branch-mutating git.
- Agent-surveyed numbers are hypotheses; committed artifacts are the source of truth — re-derive before writing prose, and guard quoted literals with re-derivation tests.
- Close-then-merge automation is not idempotent: check forge state (`gh pr view --json state`) before retrying any merge step — a bounced-looking run may already have queued the merge.
- Negative guards + label contracts let prose restructure freely; positive wording pins force test-chasing — editorial intent lives in the brief, not in CI (polarity rule).

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

## User Preferences
- [Linux only](user_platform.md) — omit macOS/Windows instructions
- Wants minimal, non-over-engineered solutions
- French-language report about Vietnamese thermal power plants as AI benchmark task

## Active
- [Reference v1 defects & pipeline](project_reference_fix1.md) — v1 scores as-is, defects documented (PROVENANCE checklist); fix1 leapfrogged, never shipped; corrections via pipe 0420→0416→0419, adoption 0413 after 0412; fix the master + regenerate, never patch downstream
- [No invented names](feedback_no_invented_names.md) — reference names must be source-attested; disambiguate structurally (status/units), never synthesize a name
- [Verbatim by construction](feedback_verbatim_by_construction.md) — line-shaped edits via grep/sed/awk + count guards, not csv round-trips; diff-vs-source is the provenance evidence
- [Three-quality argument](project_three_quality_argument.md) — paper's spine: data / answer / method, four limits split 2/2, method quality is perpendicular not a fifth limit (ticket chain 0145–0154)
- [Coherence axis decomposition](project_coherence_axis_decomposition.md) — Coherence dimension → internal/external reference-free composites, per-row pass/fail; + `level` enum dimension (granularity, capacity plausibility is level-conditional); ticket chain 0201→0396→0397, 0401→0402
- [Econom'IA 2026](project_economia_2026.md) — talk delivered & archived: tag economia-2026-cergy (bbc4a013), HAL hal-05644906, release with presented PDF
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
- [Zotero library](reference_zotero.md) — userID 95318, API keys in ~/.claude/.env, collection T4X7ZNQL
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
- [Local 9B near ceiling](project_local_9b_near_ceiling.md) — qwen3.5:9b at F1=0.984 on direct (n=1); may collapse priority-3 scope if reproduces
- [Pydantic unknown kwargs](feedback_pydantic_unknown_kwargs.md) — test schema *projection effects* (asymmetric values), not literal construction; BaseModel accepts unknown kwargs silently
- [STRUCTURED_DIRS registry](project_structured_dirs_registry.md) — Makefile has hardcoded sweep-dir list; new outputs must be registered or extract skips them
- [Ticket housekeeping via PR](feedback_ticket_housekeeping_on_main.md) — ALL main-targeted commits (tickets, STATE) go through branch+PR; GH006 branch protection rejects direct pushes; merge with `--merge --auto`, never squash
- [gaze fork dies in bg jobs](feedback_gaze_fork_dies_in_background_jobs.md) — in background sessions run sonnet reviewers + /verify-gate directly; /gaze's forked reviewers evaporate
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
