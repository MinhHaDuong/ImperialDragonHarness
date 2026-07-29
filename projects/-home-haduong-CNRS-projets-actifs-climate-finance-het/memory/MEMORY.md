# Project Memory

## Key insights
- 4-paper research programme (`climate-finance-het`); RDJ-26561 revision 1 resubmitted 2026-07-29, awaiting editor. Œconomia v2.0.5 resubmitted 2026-07-21, awaiting editor. Submission records live under `papiers/<state>/<track>/`.
- **Methodological honesty is a hard norm**: computation *corroborates* history; cite only pipeline numbers traceable to an archived output.
- **Heavy worktree + parallel-session discipline**: shared uv env on /data, never rebase with dirty DVC symlinks, branch-before-edit, check filesystem before asserting work undone.
- Author optimizes for **diamond-OA integrity over prestige** (no APC, CNRS Section 41), HET academic register, weekends off.
- **Two-machine flow** (doudou ↔ padme): data flows padme→doudou only; uv absent from non-interactive PATH; phase separation (manuscript build never triggers Phase 1).

## ⚠️ Read first — project relocated/renamed 2026-06-19
- [Reorg 0159 relocation](project_reorg_0159_relocation.md) — engine now `~/CNRS/projets/actifs/climate-finance-het/`; older memories referencing the old path/name are stale.

## Project facts
- Corpus: full = "scholarship around climate finance"; core subset = `cited_by_count >= 50`.
- Three-act periodization (I 1990–2006 / II 2007–2014, breaks 2007+2013 / III 2015–2025, Paris marginal): history-first, corpus corroborates. See [[feedback_oversell_breaks]].
- Œconomia figure decisions: user rejected the z-score plot, a hand-curated Table 1, inset legend swatches.
- Parked ideas: `docs/braindump-2026-03-18.md`; [project_ollama_experiment.md](project_ollama_experiment.md).
- [project_includes_citation_guard_0244.md](project_includes_citation_guard_0244.md) — citation guard now covers `_includes/`; 5 AI-generated includes still carry unreviewed-by-design markers.

## User & workflow
- [user_cnrs_section41.md](user_cnrs_section41.md), [user_orcid.md](user_orcid.md) (ORCID 0000-0001-9988-2100, never guess), [user_moa_moe_contract.md](user_moa_moe_contract.md) (user MOA, Claude MOE).
- Preferences: autonomous search; worktrees for branches; a PR per ticket; runs parallel sessions — don't assume files are stale.
- [reference_agent_identity.md](reference_agent_identity.md) — HDMX-coding-agent is a git-author alias; GH actions appear as MinhHaDuong; `--comment` not `--approve` for self-review.

## Machines, data & tools
- **padme**: repo `~/Climate_finance`; `uv` at `~/.local/bin/uv` (prepend PATH non-interactively); torch `--extra cpu` (doudou) / `--extra cu130` (padme); cache config in `/etc/environment`.
- **OpenRouter**: key in `~/.bashrc`; background bash doesn't inherit — export explicitly; request flat JSON keys.
- **OpenAlex**: premium key in `.env`; S2 key in docs/ (1 req/s); JETP query disabled.
- **Perf**: never `iterrows()` on 20K+ DataFrames.
- [project_uv_path_fix.md](project_uv_path_fix.md), [project_worktree_env_data.md](project_worktree_env_data.md), [project_doifetch_sync.md](project_doifetch_sync.md), [project_dvc_integration.md](project_dvc_integration.md).

## Papers & submission
- RDJ-26561 R&R round 1: [project_rdj26561_rr_round1.md](project_rdj26561_rr_round1.md) — COMPLETE, revision 1 resubmitted 2026-07-29; upload-kit recipe for round 2 inside.
- [project_prior_mappings_overlap_0289.md](project_prior_mappings_overlap_0289.md) — prior-mappings overlap probe: 89–91% coverage = curation, >99% discovery; artifacts in revision-rdj26561/; feeds 0278/0283.
- Œconomia R&R: [project_oeconomia_rr_pipeline.md](project_oeconomia_rr_pipeline.md), [project_rr_traceability_ledger.md](project_rr_traceability_ledger.md), [project_0171_conclusion_rebuild.md](project_0171_conclusion_rebuild.md), [feedback_version_increment_planning.md](feedback_version_increment_planning.md).
- Reports & build: [project_techrep_rewrite.md](project_techrep_rewrite.md), [project_techrep_split.md](project_techrep_split.md), [project_writing_build_phase_separation.md](project_writing_build_phase_separation.md), [project_frozen_manuscript_vs_live_companions.md](project_frozen_manuscript_vs_live_companions.md), [project_repo_layout_decision.md](project_repo_layout_decision.md), [project_deliverables_render_next_to_source.md](project_deliverables_render_next_to_source.md).
- Next papers: [project_paper_ceiling_growth_imaginary.md](project_paper_ceiling_growth_imaginary.md), [project_paper_instrument_circulation.md](project_paper_instrument_circulation.md).
- Journals: [project_journal_strategy.md](project_journal_strategy.md), [reference_rdj4hss.md](reference_rdj4hss.md), [project_gide_conference.md](project_gide_conference.md).
- Biblio: [reference_bib_fulltext_index.md](reference_bib_fulltext_index.md), [reference_cited_works_local_docs_articles.md](reference_cited_works_local_docs_articles.md), [reference_paywalled_acquisition.md](reference_paywalled_acquisition.md), [reference_publist.md](reference_publist.md).
- [reference_hal_sword_update_recipe.md](reference_hal_sword_update_recipe.md) — SWORD new-version: filename=meta.xml, dotted JEL, CDATA password mask trap
- Tooling: OPIDoR DMP import — select "RDA" in the format picker. [feedback_quarto_var_vs_meta.md](feedback_quarto_var_vs_meta.md), [reference_trackchange_review_workflow.md](reference_trackchange_review_workflow.md).

## Harness & telemetry
- [project_imperial_dragon.md](project_imperial_dragon.md), [reference_stats_cache.md](reference_stats_cache.md), [reference_agentic_harness.md](reference_agentic_harness.md), [reference_repo_no_ci.md](reference_repo_no_ci.md).

## Feedback
- [feedback_erg_close_archive.md](feedback_erg_close_archive.md) — `erg close`/`erg archive` are separate; run both pre-PR
- [feedback_prclose_onbranch_ticket_none.md](feedback_prclose_onbranch_ticket_none.md) — ticket closed on-branch → PR needs `Ticket: none`, not the archived path
- [feedback_het_register.md](feedback_het_register.md) — manuscript prose = HET academic register, not motivational cadence
- [feedback_no_long_running.md](feedback_no_long_running.md) — don't launch long-running tasks (make, rendering); let user run in terminal
- [feedback_render_bitcompare_is_the_gate.md](feedback_render_bitcompare_is_the_gate.md) — for a pure build refactor, render old-vs-new + byte-compare IS the validation gate
- [feedback_phase_separation.md](feedback_phase_separation.md) — make manuscript must never trigger Phase 1 scripts/API calls
- [feedback_data_direction.md](feedback_data_direction.md) — data flows padme→doudou only
- [feedback_no_heavy_deps.md](feedback_no_heavy_deps.md) — don't add heavy deps when a simple approach works
- [feedback_review_agent_worktree.md](feedback_review_agent_worktree.md) — review agents must read from PR branch worktree, not main
- [feedback_overnight_exploration.md](feedback_overnight_exploration.md) — overnight sessions prioritize deliverables, not just tooling
- [feedback_no_apc.md](feedback_no_apc.md) — APCs are scams; choose diamond OA venues
- [feedback_parallel_work.md](feedback_parallel_work.md) — user works in parallel; check filesystem before assuming work undone
- [feedback_no_amend_pr.md](feedback_no_amend_pr.md) — don't amend commits on open PRs
- [feedback_verify_ai_generated_includes.md](feedback_verify_ai_generated_includes.md) — never cite an unreviewed AI-generated include without verifying
- [feedback_letter_voice_flags.md](feedback_letter_voice_flags.md) — align prose on style-anchor-v205 BEFORE showing it; letters 1st person singular
- [feedback_a4_paper.md](feedback_a4_paper.md) — always A4, never US letter
- [feedback_no_md_in_md.md](feedback_no_md_in_md.md) — never put markdown headings inside fenced blocks
- [feedback_worktree_search.md](feedback_worktree_search.md) — scan parent dirs and /tmp for stale worktrees, not just `git worktree list`
- [feedback_no_noverify.md](feedback_no_noverify.md) — never bypass pre-commit hooks with --no-verify
- [feedback_worktree_local_hook_commit.md](feedback_worktree_local_hook_commit.md) — commit a branch's own hook fix via `git -c core.hooksPath=<worktree>/hooks`
- [feedback_branch_before_edit.md](feedback_branch_before_edit.md) — checkout target branch before editing; never edit on main then move
- [feedback_make_corpus.md](feedback_make_corpus.md) — never bare `dvc repro`; use `make corpus`/`make corpus-sync`
- [feedback_no_rebase_dvc.md](feedback_no_rebase_dvc.md) — never rebase with dirty DVC symlinks; merge + stash/pop
- [feedback_simplest_fix.md](feedback_simplest_fix.md) — restructure to work within existing rules, don't add hooks/exceptions
- [feedback_ssh_padme.md](feedback_ssh_padme.md) — can SSH doudou→padme; prepend PATH=$HOME/.local/bin
- [feedback_weekend_boundary.md](feedback_weekend_boundary.md) — no project work on weekends
- [feedback_verify_before_advising.md](feedback_verify_before_advising.md) — WebFetch conference/journal URLs before strategic advice
- [feedback_dropna_before_merge.md](feedback_dropna_before_merge.md) — dropna before merge/set_index on DOI (NaN==NaN cartesian explosion)
- [feedback_escalate_check_merge_after_note.md](feedback_escalate_check_merge_after_note.md) — after a verify-gate ESCALATE, check if the PR merged anyway before assuming more work is needed
- [feedback_grep_before_commit.md](feedback_grep_before_commit.md) — grep whole project before committing pattern fixes
- [feedback_inspect_ref_readonly.md](feedback_inspect_ref_readonly.md) — inspect another ref with git grep/show, never checkout
- [feedback_oversell_breaks.md](feedback_oversell_breaks.md) — computation corroborates history, not the reverse
- [feedback_tectonic_next.md](feedback_tectonic_next.md) — next project: Tectonic + plain LaTeX, not Quarto
- [feedback_verify_deferral_tracker.md](feedback_verify_deferral_tracker.md) — verify deferral tracker still open/in-scope before closing
- [feedback_no_tool_for_single_use.md](feedback_no_tool_for_single_use.md) — single-use op → run the command, don't build a tool
- [feedback_file_decisions_with_submission.md](feedback_file_decisions_with_submission.md) — file journal decisions as tracked text beside the submission folder
- [feedback_manuscript_number_provenance.md](feedback_manuscript_number_provenance.md) — cite only pipeline numbers traceable to an archived output
- [feedback_read_before_cite.md](feedback_read_before_cite.md) — a reference enters the manuscript only after being read and argued relevant
- [feedback_fetch_before_sibling_merge.md](feedback_fetch_before_sibling_merge.md) — multi-PR wave on one file: fetch before each sibling merge, grep-verify the union
- [feedback_sibling_close_collides_on_shared_blocker.md](feedback_sibling_close_collides_on_shared_blocker.md) — sibling erg closes collide on a shared Blocked-by ticket; pre-merge main into each next sibling before erg-pr-merge
- [feedback_atomic_tickets_validation_units.md](feedback_atomic_tickets_validation_units.md) — tickets must be atomic — one MOA validation unit per ticket/PR
- [feedback_bytecheck_old_vs_new_not_golden.md](feedback_bytecheck_old_vs_new_not_golden.md) — byte-check old vs new code on the SAME current data, never a committed golden
- [feedback_caps_force_pruning_not_compression.md](feedback_caps_force_pruning_not_compression.md) — a size cap forces pruning stale content, never compression to game the number
- [feedback_cite_at_existing_locus.md](feedback_cite_at_existing_locus.md) — find the passage that already makes the point before adding a referee-requested citation
- [feedback_cross_repo_ticket_in_owning_repo.md](feedback_cross_repo_ticket_in_owning_repo.md) — file a follow-up ticket in the repo that OWNS the target file
- [feedback_decide_dont_micromanage.md](feedback_decide_dont_micromanage.md) — decide across the whole logical unit; don't hardcode/half-do/ask piecemeal
- [feedback_followup_lets_parent_close.md](feedback_followup_lets_parent_close.md) — a follow-up ticket exists so the parent can CLOSE now
- [feedback_gate_after_full_review.md](feedback_gate_after_full_review.md) — don't run verify-gate until the full review fan-out has returned
- [feedback_hitl_decision_cite_evidence.md](feedback_hitl_decision_cite_evidence.md) — record an author's HITL decision with evidence a diff-only reviewer can verify
- [feedback_isolated_venv_proves_installability.md](feedback_isolated_venv_proves_installability.md) — test package install in a fresh isolated venv, not an env that already has the dep
- [feedback_no_shared_env_sync_during_sibling_agent.md](feedback_no_shared_env_sync_during_sibling_agent.md) — never uv sync the shared /data env while a sibling agent is mid-run
- [feedback_pilot_one_instance_critiques_the_ticket.md](feedback_pilot_one_instance_critiques_the_ticket.md) — pilot one instance read-only before building a ticket-spec'd analysis; it can falsify the design
- [feedback_pin_test_mutation_teeth.md](feedback_pin_test_mutation_teeth.md) — prove a regression-pin test's teeth by mutating the guarded mechanism
- [feedback_pr_creates_ticket_no_close.md](feedback_pr_creates_ticket_no_close.md) — a PR that FILES a new ticket uses Ticket-ref / Ticket none, never **Ticket:**
- [feedback_propagate_notes_to_tickets.md](feedback_propagate_notes_to_tickets.md) — session notes assigning inputs to tickets must be written INTO those tickets at once
- [feedback_ratchet_stale_after_rebuild.md](feedback_ratchet_stale_after_rebuild.md) — a green prose-ratchet doesn't mean ceilings match current text — a rebuild leaves them stale
- [feedback_reorg_tracker_first_class_guard.md](feedback_reorg_tracker_first_class_guard.md) — multi-ticket reorg needs a tracker filed BEFORE executing; guards must be class-level
- [feedback_rule9_detector_variable_path_blindspot.md](feedback_rule9_detector_variable_path_blindspot.md) — arch-rule-9 misses contract reads via a path variable
- [feedback_settled_debates_to_brief.md](feedback_settled_debates_to_brief.md) — a settled debate goes into the enforced register (editorial brief) at settlement time
- [feedback_stale_worktree_make.md](feedback_stale_worktree_make.md) — after merging from a worktree, run make from the main checkout
- [feedback_verify_active_before_defer_tag.md](feedback_verify_active_before_defer_tag.md) — before a bulk defer-tag pass, verify no ticket is being actively worked
- [feedback_agent_prompt_worktree_rooted_paths.md](feedback_agent_prompt_worktree_rooted_paths.md) — a worktree-isolated Agent prompt uses repo-relative paths, never primary-checkout absolute paths
- [feedback_gate_execute_on_all_scopers.md](feedback_gate_execute_on_all_scopers.md) — gate a raid's execute wave on ALL scopers returning, not a quorum
- [feedback_verify_datadep_worktree_symlink.md](feedback_verify_datadep_worktree_symlink.md) — validate a data-dependent Makefile change in a worktree by symlinking primary checkout's contract files
- [feedback_aitells_scope_manuscript_vs_crossdoc.md](feedback_aitells_scope_manuscript_vs_crossdoc.md) — ai-tells.yml blacklisted_words feeds a cross-document guard; a per-document house-style choice goes in a scoped test
- [feedback_negative_guard_false_positive_check.md](feedback_negative_guard_false_positive_check.md) — run the prose suite right after adding a forbidden-phrase guard; generic candidates collide with legitimate prose
- [feedback_verify_makefile_pathrefactor_with_make_n.md](feedback_verify_makefile_pathrefactor_with_make_n.md) — verify a Makefile path refactor with `make -n` + spot-check + grep
- [feedback_visual_verify_citations.md](feedback_visual_verify_citations.md) — render the PDF and eyeball it — catches citation/bib errors grep and CI cannot
- [feedback_ruff_fix_breaks_reexport_facades.md](feedback_ruff_fix_breaks_reexport_facades.md) — ruff --fix silently guts re-export facades; probe reach-through imports after
- [feedback_evict_to_gitignored_dir_bootstrap.md](feedback_evict_to_gitignored_dir_bootstrap.md) — moving output to a gitignored dir removes the free dir-bootstrap; producers must os.makedirs first
- [feedback_moving_files_narrows_guard_globs.md](feedback_moving_files_narrows_guard_globs.md) — relocating files silently narrows fixed-dir guard globs; sweep ALL enumeration sites
- [feedback_raid_scope_triage_before_fanout.md](feedback_raid_scope_triage_before_fanout.md) — a /raid over N tickets isn't auto an N-wide fan-out; triage chains/conflicts first
- [feedback_raid_overkill_for_trivial_reference_pattern_fix.md](feedback_raid_overkill_for_trivial_reference_pattern_fix.md) — don't run full raid/gaze on a trivial fix with an exact reference pattern; 42min for a 3-line change, "that's glacial"
- [project_file_relocation_move_surface.md](project_file_relocation_move_surface.md) — relocating a scripts/ entry point touches 8 surfaces, not just git mv
- [feedback_hardcoded_secondary_path_survives_input_gate.md](feedback_hardcoded_secondary_path_survives_input_gate.md) — an --input-gated primary read can hide a hardcoded secondary-file path bug until the harness actually reaches it; sweep sibling scripts for the same shape
- [feedback_interactive_authorization_invisible_to_gates.md](feedback_interactive_authorization_invisible_to_gates.md) — a mechanical gate only sees committed text (PR body, ticket invariant); live-conversation author authorization is invisible to it and can trigger a false-positive REROLL
- [feedback_verify_new_citations_against_primary_pdf.md](feedback_verify_new_citations_against_primary_pdf.md) — grep the locally staged primary-source PDF for the exact claim before finalizing a citation; caught 3 real errors in one session
- [feedback_gate_verify_branch_not_pr_body.md](feedback_gate_verify_branch_not_pr_body.md) — gate on actual branch/test state at HEAD, never trust the PR body as evidence
- [feedback_user_pulls_land_in_downloads.md](feedback_user_pulls_land_in_downloads.md) — a manual user PDF pull lands in ~/Downloads/, check there before asking
- [feedback_fable_second_opinion_prose_structure.md](feedback_fable_second_opinion_prose_structure.md) — Fable as independent reviewer for manuscript structural TODOs gave concrete, actionable recommendations
- [feedback_background_session_manuscript_pr_workflow.md](feedback_background_session_manuscript_pr_workflow.md) — background sessions force worktree+PR even for prose-in-place; reconcile primary checkout's stale uncommitted diff after merge
- [feedback_pdf_layout_automate_dont_hand_paginate.md](feedback_pdf_layout_automate_dont_hand_paginate.md) — automate pagination (titlesec sectionbreak, widow penalties, dash-ratio col widths); variant builds = transform layer script
- [feedback_rtk_log_hides_merge_commits.md](feedback_rtk_log_hides_merge_commits.md) — rtk-filtered `git log` omits merge commits; verify tips with rev-parse / `rtk proxy git log`
- [feedback_pdftotext_grep_linebreaks.md](feedback_pdftotext_grep_linebreaks.md) — line-based grep on pdftotext output false-negatives across line wraps; join text before matching
