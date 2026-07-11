# Project Memory

## Key insights
- The repo is a **4-paper research programme** (`climate-finance-het`); the Œconomia R&R is the active deadline track, run as a version ladder (v2.0.3 → v2.0.5) gated by tracker tickets. Submission records live outside the repo under `papiers/<state>/<track>/`.
- **Methodological honesty is a hard norm**: computation *corroborates* history (don't oversell breaks / claim "Paris didn't matter"); cite only pipeline numbers traceable to an archived output.
- **Heavy worktree + parallel-session discipline**: shared uv env on /data, data on-demand, never rebase with dirty DVC symlinks, branch-before-edit, check the filesystem before asserting work undone.
- The author optimizes for **diamond-OA integrity over prestige** (no APC, CNRS Section 41), an HET academic register (not motivational), and weekends off.
- **Two-machine flow** (doudou ↔ padme): data flows padme→doudou only; uv isn't in non-interactive PATH; phase separation (a manuscript build never triggers Phase 1).

## ⚠️ Read first — project relocated/renamed 2026-06-19
- [Reorg 0159 relocation](project_reorg_0159_relocation.md) — engine now `~/CNRS/projets/actifs/climate-finance-het/` (GitHub `climate-finance-het`); records in `papiers/<state>/<track>/`; older memories referencing the old path/name are stale. Follow-up: ticket 0160.

## Project facts
- Corpus: full = "scholarship around climate finance" (not "climate finance scholarship" — too narrow); core subset = `cited_by_count >= 50` (influential works).
- Three-act periodization (I 1990–2006 / II 2007–2014, breaks 2007+2013 / III 2015–2025, Paris marginal): history-first, corpus corroborates (detection blind to COP calendar). Full detail in `writing.md` rule; see [[feedback_oversell_breaks]].
- Œconomia figure decisions: user rejected the z-score plot ("too technical for HPS"), a hand-curated Table 1 ("I want code. Clustering to DETECT."), and inset legend swatches ("failed idea").
- Parked ideas (post-submission): `docs/braindump-2026-03-18.md`; [project_ollama_experiment.md](project_ollama_experiment.md).

## User & workflow
- [user_cnrs_section41.md](user_cnrs_section41.md) — CNRS Section 41; peer-reviewed HPS/STS credibility over IF. [user_orcid.md](user_orcid.md) — ORCID 0000-0001-9988-2100 (never guess). [user_moa_moe_contract.md](user_moa_moe_contract.md) — user is MOA, Claude is MOE.
- Preferences: autonomous for all search (don't stop to ask); worktrees for branches; a PR per ticket (reviews via GitHub); runs parallel sessions — don't assume files are stale.
- [reference_agent_identity.md](reference_agent_identity.md) — HDMX-coding-agent is a git-author alias; GH actions appear as MinhHaDuong; use `--comment` not `--approve` for self-review.

## Machines, data & tools
- **padme** (remote): repo `~/Climate_finance` (NOT under ~/CNRS/); `uv` at `~/.local/bin/uv` (absent from non-interactive PATH — prepend `PATH=$HOME/.local/bin`); GPUs A4000 16GB + RTX 3060 12GB; torch extras `--extra cpu` (doudou) / `--extra cu130` (padme); cache config in `/etc/environment` (non-interactive SSH skips `/etc/profile.d/`); Ollama often ~19GB RSS; `nohup` long tasks, logs in `/tmp/`.
- **OpenRouter**: key in `~/.bashrc` (OPENROUTER_API_KEY); background bash doesn't inherit — export explicitly; request flat JSON keys (LLMs default to numbered).
- **OpenAlex**: premium key ($2/day) in `.env`; S2 key in docs/ (1 req/s even with key); JETP query disabled (ambiguous acronym, physics-journal noise).
- **Perf**: never `iterrows()` on 20K+ DataFrames — vectorize with pandas masks.
- Toolchain/data ops: [project_uv_path_fix.md](project_uv_path_fix.md), [project_worktree_env_data.md](project_worktree_env_data.md), [project_doifetch_sync.md](project_doifetch_sync.md), [project_dvc_integration.md](project_dvc_integration.md).

## Papers & submission
- Œconomia R&R: [project_oeconomia_rr_pipeline.md](project_oeconomia_rr_pipeline.md) (version ladder), [project_rr_traceability_ledger.md](project_rr_traceability_ledger.md) (60-remark ledger + HITL sign-off), [project_0171_conclusion_rebuild.md](project_0171_conclusion_rebuild.md), [feedback_version_increment_planning.md](feedback_version_increment_planning.md).
- Reports & build: [project_techrep_rewrite.md](project_techrep_rewrite.md), [project_techrep_split.md](project_techrep_split.md), [project_writing_build_phase_separation.md](project_writing_build_phase_separation.md), [project_frozen_manuscript_vs_live_companions.md](project_frozen_manuscript_vs_live_companions.md), [project_repo_layout_decision.md](project_repo_layout_decision.md), [project_deliverables_render_next_to_source.md](project_deliverables_render_next_to_source.md) (raid 237 — deliverables/ landed, output/ retired).
- Next papers: [project_paper_ceiling_growth_imaginary.md](project_paper_ceiling_growth_imaginary.md), [project_paper_instrument_circulation.md](project_paper_instrument_circulation.md).
- Journals: [project_journal_strategy.md](project_journal_strategy.md), [reference_rdj4hss.md](reference_rdj4hss.md), [project_gide_conference.md](project_gide_conference.md).
- Biblio & cited-works gate: [reference_bib_fulltext_index.md](reference_bib_fulltext_index.md), [reference_cited_works_local_docs_articles.md](reference_cited_works_local_docs_articles.md), [reference_paywalled_acquisition.md](reference_paywalled_acquisition.md), [reference_publist.md](reference_publist.md).
- Tooling: OPIDoR DMP import — use RDA/maDMP JSON, select "RDA" in the format picker (UI switches to English after). [feedback_quarto_var_vs_meta.md](feedback_quarto_var_vs_meta.md), [reference_trackchange_review_workflow.md](reference_trackchange_review_workflow.md).

## Harness & telemetry
- [project_imperial_dragon.md](project_imperial_dragon.md), [reference_stats_cache.md](reference_stats_cache.md), [reference_agentic_harness.md](reference_agentic_harness.md), [reference_repo_no_ci.md](reference_repo_no_ci.md).

## Feedback
- [feedback_erg_close_archive.md](feedback_erg_close_archive.md) — PROVISIONAL: `erg close` and `erg archive` are separate; run both when closing pre-PR or /gaze flags the unarchived ticket (burned a round on 0149)
- [feedback_prclose_onbranch_ticket_none.md](feedback_prclose_onbranch_ticket_none.md) — ticket closed+archived on-branch → PR body needs `Ticket: none`, not `**Ticket:** tickets/closed/NNNN` (erg-pr-merge rejects the archived path; burned 2 retries on #1000)
- [feedback_enterworktree_stuck_cwd.md](feedback_enterworktree_stuck_cwd.md) — EnterWorktree/cwd-skills target the wrong repo when session base cwd is parked off-project; fall back to manual `git worktree add` + `git -C`
- [feedback_het_register.md](feedback_het_register.md) — manuscript prose = HET academic register, not American motivational/business-book cadence
- [feedback_yaml_quoting.md](feedback_yaml_quoting.md) — use `'"phrase"'` not `"phrase"` in corpus_collect.yaml for phrase search queries
- [feedback_no_long_running.md](feedback_no_long_running.md) — don't launch long-running tasks (make, rendering); let user run in their terminal
- [feedback_render_bitcompare_is_the_gate.md](feedback_render_bitcompare_is_the_gate.md) — for a pure build/layout refactor, render old-vs-new + byte-compare content is THE validation gate (clean-room manuscript is ~12s, SOURCE_DATE_EPOCH=0); don't over-apply no-long-running to skip it
- [feedback_phase_separation.md](feedback_phase_separation.md) — make manuscript must never trigger Phase 1 scripts or API calls
- [feedback_data_direction.md](feedback_data_direction.md) — data flows padme→doudou only; never push data from doudou to padme
- [feedback_no_heavy_deps.md](feedback_no_heavy_deps.md) — don't add heavy deps (jupyter) when a simple approach (YAML, hardcode) works
- [feedback_review_agent_worktree.md](feedback_review_agent_worktree.md) — review agents must read from PR branch worktree, not main
- [feedback_overnight_exploration.md](feedback_overnight_exploration.md) — overnight sessions must prioritize deliverables (next paper), not just tooling; use runbooks/overnight-exploration.md
- [feedback_no_apc.md](feedback_no_apc.md) — APCs are scams; choose diamond OA venues (integrity, excellence, care)
- [feedback_parallel_work.md](feedback_parallel_work.md) — user works in VSCode terminal in parallel; check filesystem before asserting something hasn't been done
- [feedback_no_amend_pr.md](feedback_no_amend_pr.md) — don't amend commits on open PRs; force push makes GitHub diffs confusing
- [feedback_verify_ai_generated_includes.md](feedback_verify_ai_generated_includes.md) — never cite from an AI-generated-not-human-reviewed include without verifying (phantom ref caught in §11)
- [feedback_letter_voice_flags.md](feedback_letter_voice_flags.md) — align prose on style-anchor-v205 BEFORE showing it (A-not-B cadence, -ly stacks, jargon); letters in 1st person singular
- [feedback_a4_paper.md](feedback_a4_paper.md) — always A4 paper format for generated PDFs, never US letter
- [feedback_no_md_in_md.md](feedback_no_md_in_md.md) — never put markdown (## headings) inside fenced blocks; extract to a real file
- [feedback_worktree_search.md](feedback_worktree_search.md) — scan parent dirs and /tmp for stale worktree directories, not just `git worktree list`
- [feedback_no_noverify.md](feedback_no_noverify.md) — never bypass pre-commit hooks with --no-verify; always branch first
- [feedback_worktree_local_hook_commit.md](feedback_worktree_local_hook_commit.md) — commit a branch's own hook fix via `git -c core.hooksPath=<worktree>/hooks` when hooksPath is absolute
- [feedback_branch_before_edit.md](feedback_branch_before_edit.md) — always checkout target branch before editing files; never edit on main then move
- [feedback_make_corpus.md](feedback_make_corpus.md) — never suggest bare `dvc repro`; always use `make corpus` (padme) or `make corpus-sync` (doudou)
- [feedback_no_rebase_dvc.md](feedback_no_rebase_dvc.md) — never rebase when DVC symlinks are dirty; use merge + stash/pop
- [feedback_ln_into_existing_dir_autostage.md](feedback_ln_into_existing_dir_autostage.md) — ln -s into an existing dir lands the link INSIDE it; dvc autostage commits the loop symlink (0252 guard: test_no_committed_symlink_under_data)
- [feedback_simplest_fix.md](feedback_simplest_fix.md) — don't add hooks/exceptions; restructure the operation to work within existing rules (ff merge vs --no-ff)
- [feedback_ssh_padme.md](feedback_ssh_padme.md) — can SSH doudou→padme; always prepend PATH=$HOME/.local/bin (uv not in non-interactive PATH)
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
- [feedback_manuscript_number_provenance.md](feedback_manuscript_number_provenance.md) — cite only pipeline numbers that trace to an archived output; v1-pinned manuscript can drift from live-pipeline stats (the 0.68 case)
- [feedback_read_before_cite.md](feedback_read_before_cite.md) — a reference enters the manuscript only after it is read and its core-relevance argued; no referee-checkbox padding
- [feedback_fetch_before_sibling_merge.md](feedback_fetch_before_sibling_merge.md) — multi-PR wave on one file: fetch before each sibling merge + grep-verify the union (also in git.md)
- [feedback_no_rebase_when_force_push_denied.md](feedback_no_rebase_when_force_push_denied.md) — force-push denied → don't rebase a pushed PR branch before merge; it strands local ahead of remote and breaks erg-pr-merge's non-idempotent close+push
- [feedback_atomic_tickets_validation_units.md](feedback_atomic_tickets_validation_units.md) — tickets must be atomic — one MOA validation unit per ticket/PR
- [feedback_bytecheck_old_vs_new_not_golden.md](feedback_bytecheck_old_vs_new_not_golden.md) — byte-check a behaviour-preserving refactor by running old vs new code on the SAME current data, never against a committed golden
- [feedback_caps_force_pruning_not_compression.md](feedback_caps_force_pruning_not_compression.md) — a line/size cap forces pruning stale content — never compression to game the number
- [feedback_cite_at_existing_locus.md](feedback_cite_at_existing_locus.md) — integrating a referee-requested citation — find the passage that already makes the point, the non-redundant locus, before adding prose
- [feedback_cross_repo_ticket_in_owning_repo.md](feedback_cross_repo_ticket_in_owning_repo.md) — file a follow-up ticket in the repo that OWNS the target file, not the consuming project that discovered the need
- [feedback_decide_dont_micromanage.md](feedback_decide_dont_micromanage.md) — make the coherent decision across the whole logical unit; don't hardcode, don't half-do, don't ask piecemeal
- [feedback_followup_lets_parent_close.md](feedback_followup_lets_parent_close.md) — a follow-up ticket exists so the parent can CLOSE now; don't keep the parent open as a pseudo-tracker
- [feedback_force_push_denied_rebuild_clean.md](feedback_force_push_denied_rebuild_clean.md) — force-push denied → rebuild the stale branch cleanly on current main (new branch, copy deliverables, fresh commit, ff push)
- [feedback_gate_after_full_review.md](feedback_gate_after_full_review.md) — don't run verify-gate until the full review fan-out (esp. correctness/red-team) has returned
- [feedback_hitl_decision_cite_evidence.md](feedback_hitl_decision_cite_evidence.md) — when recording an author's HITL decision, cite the evidence so a diff-only reviewer can verify it
- [feedback_isolated_venv_proves_installability.md](feedback_isolated_venv_proves_installability.md) — green tests from an env that already has a dep don't prove a package installs; test in a fresh isolated venv
- [feedback_no_shared_env_sync_during_sibling_agent.md](feedback_no_shared_env_sync_during_sibling_agent.md) — never uv sync the shared /data env while a sibling background agent is mid-run
- [feedback_pilot_one_instance_critiques_the_ticket.md](feedback_pilot_one_instance_critiques_the_ticket.md) — before building a compute_*.py analysis from a ticket spec, pilot one instance read-only — it can falsify the ticket's design
- [feedback_pin_test_mutation_teeth.md](feedback_pin_test_mutation_teeth.md) — a regression-pin test passes on current behaviour; prove its teeth by mutating the guarded mechanism
- [feedback_pr_creates_ticket_no_close.md](feedback_pr_creates_ticket_no_close.md) — a PR that FILES a new follow-up ticket must use Ticket-ref / Ticket none — never **Ticket:**
- [feedback_propagate_notes_to_tickets.md](feedback_propagate_notes_to_tickets.md) — session notes that assign inputs to tickets must be written INTO those tickets at once; Execute agents start cold
- [feedback_ratchet_stale_after_rebuild.md](feedback_ratchet_stale_after_rebuild.md) — a green prose-ratchet suite doesn't mean the ceilings match the current manuscript — a base rebuild leaves them stale
- [feedback_reorg_tracker_first_class_guard.md](feedback_reorg_tracker_first_class_guard.md) — multi-ticket reorg needs a tracker filed BEFORE executing, and guards must be class-level, not per-file whitelists
- [feedback_rule9_detector_variable_path_blindspot.md](feedback_rule9_detector_variable_path_blindspot.md) — the arch-rule-9 test misses contract reads via a path variable (matches read-call and filename on the SAME line only)
- [feedback_settled_debates_to_brief.md](feedback_settled_debates_to_brief.md) — a settled debate must be written into the enforced register (editorial brief) at settlement time, or it gets re-litigated
- [feedback_stale_worktree_make.md](feedback_stale_worktree_make.md) — after merging from a worktree, the session stays bound to it; run make from the main checkout
- [feedback_verify_active_before_defer_tag.md](feedback_verify_active_before_defer_tag.md) — before a bulk defer-tag/triage pass, fetch origin/main and verify no ticket is being actively worked
- [feedback_agent_prompt_worktree_rooted_paths.md](feedback_agent_prompt_worktree_rooted_paths.md) — a worktree-isolated Agent prompt must use repo-relative paths, never the primary-checkout absolute path
- [feedback_gate_execute_on_all_scopers.md](feedback_gate_execute_on_all_scopers.md) — gate a raid's execute wave on ALL scopers returning, not a quorum; the late scoper often carries the scope-narrowing finding
- [feedback_verify_datadep_worktree_symlink.md](feedback_verify_datadep_worktree_symlink.md) — validate a data-dependent Makefile/Phase-2 change in a worktree by symlinking the primary checkout's contract files
- [feedback_verify_makefile_pathrefactor_with_make_n.md](feedback_verify_makefile_pathrefactor_with_make_n.md) — verify a Makefile path/variable refactor with `make -n` + one runtime spot-check + grep; a full downstream build is the wrong gate
- [feedback_visual_verify_citations.md](feedback_visual_verify_citations.md) — render the PDF and eyeball it — visual verification catches citation/bib errors grep and CI cannot
- [feedback_ruff_fix_breaks_reexport_facades.md](feedback_ruff_fix_breaks_reexport_facades.md) — ruff --fix silently guts re-export facades; probe reach-through imports after, and per-file-ignores go stale on rename (0232)
- [feedback_evict_to_gitignored_dir_bootstrap.md](feedback_evict_to_gitignored_dir_bootstrap.md) — moving a pipeline output to a gitignored dir removes the free dir-bootstrap; validate_io producers must os.makedirs first
- [feedback_moving_files_narrows_guard_globs.md](feedback_moving_files_narrows_guard_globs.md) — relocating files silently narrows fixed-dir guard globs; sweep ALL enumeration sites, a green suite hides the lost coverage (0239→0248)
- [feedback_raid_scope_triage_before_fanout.md](feedback_raid_scope_triage_before_fanout.md) — a /raid over N tickets isn't auto an N-wide fan-out; triage for chains, shared-subtree conflict, data-heavy gates and degrade to the safe subset (raid 240/241/242/248 → ran 248+242, held 240/241)
- [project_file_relocation_move_surface.md](project_file_relocation_move_surface.md) — relocating a scripts/ entry point touches 8 surfaces (build/dvc/tests-3-kinds/docs/pyproject/subprocess-cwd/guard-predicates/archive-cp), not just git mv; verify by recipe-identity + repo-wide union grep at integration (0240 reorg)
