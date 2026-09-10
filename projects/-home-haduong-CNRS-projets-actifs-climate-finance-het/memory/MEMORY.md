# Project Memory

## Key insights
- 4-paper research programme (`climate-finance-het`); RDJ-26561 revision 1 resubmitted 2026-07-29, awaiting editor. Œconomia v2.0.5 resubmitted 2026-07-21, awaiting editor. Submission records live under `papiers/<state>/<track>/`.
- **Methodological honesty is a hard norm**: computation *corroborates* history; cite only pipeline numbers traceable to an archived output.
- **Heavy worktree + parallel-session discipline**: shared uv env on /data, never rebase with dirty DVC symlinks, branch-before-edit, check filesystem before asserting work undone.
- Author optimizes for **diamond-OA integrity over prestige** (no APC, CNRS Section 41), HET academic register, weekends off.
- **Two-machine flow** (doudou ↔ padme): data flows padme→doudou only; uv absent from non-interactive PATH; phase separation (manuscript build never triggers Phase 1).

## ⚠️ Read first — project relocated/renamed 2026-06-19
- [Reorg 0159 relocation](project_reorg_0159_relocation.md)

## Project facts
- Corpus: full = "scholarship around climate finance"; core subset = `cited_by_count >= 50`.
- Three-act periodization (I 1990–2006 / II 2007–2014, breaks 2007+2013 / III 2015–2025, Paris marginal): history-first, corpus corroborates. See [[feedback_oversell_breaks]].
- Œconomia figure decisions: user rejected the z-score plot, a hand-curated Table 1, inset legend swatches.
- Parked ideas: `docs/braindump-2026-03-18.md`; [project_ollama_experiment.md](project_ollama_experiment.md).
- [The cited-works guard covers _includes/, not just top-level .qmd](project_includes_citation_guard_0244.md)

## User & workflow
- [user_cnrs_section41.md](user_cnrs_section41.md), [user_orcid.md](user_orcid.md) (ORCID 0000-0001-9988-2100, never guess), [user_moa_moe_contract.md](user_moa_moe_contract.md) (user MOA, Claude MOE).
- Preferences: autonomous search; worktrees for branches; a PR per ticket; runs parallel sessions — don't assume files are stale.
- [Agent GitHub identity](reference_agent_identity.md)

## Machines, data & tools
- **padme**: repo `~/Climate_finance`; `uv` at `~/.local/bin/uv` (prepend PATH non-interactively); torch `--extra cpu` (doudou) / `--extra cu130` (padme); cache config in `/etc/environment`.
- **OpenRouter**: key in `~/.bashrc`; background bash doesn't inherit — export explicitly; request flat JSON keys.
- **OpenAlex**: premium key in `.env`; S2 key in docs/ (1 req/s); JETP query disabled.
- **Perf**: never `iterrows()` on 20K+ DataFrames.
- [project_uv_path_fix.md](project_uv_path_fix.md), [project_worktree_env_data.md](project_worktree_env_data.md), [project_doifetch_sync.md](project_doifetch_sync.md), [project_dvc_integration.md](project_dvc_integration.md).

## Papers & submission
- RDJ-26561 R&R round 1: [project_rdj26561_rr_round1.md](project_rdj26561_rr_round1.md) — COMPLETE, revision 1 resubmitted 2026-07-29; upload-kit recipe for round 2 inside.
- [Refined corpus overlaps prior mappings 89–91%, discovery above 99%](project_prior_mappings_overlap_0289.md)
- Œconomia R&R: [project_oeconomia_rr_pipeline.md](project_oeconomia_rr_pipeline.md), [project_rr_traceability_ledger.md](project_rr_traceability_ledger.md), [project_0171_conclusion_rebuild.md](project_0171_conclusion_rebuild.md), [feedback_version_increment_planning.md](feedback_version_increment_planning.md).
- Reports & build: [project_techrep_rewrite.md](project_techrep_rewrite.md), [project_techrep_split.md](project_techrep_split.md), [project_writing_build_phase_separation.md](project_writing_build_phase_separation.md), [project_frozen_manuscript_vs_live_companions.md](project_frozen_manuscript_vs_live_companions.md), [project_repo_layout_decision.md](project_repo_layout_decision.md), [project_deliverables_render_next_to_source.md](project_deliverables_render_next_to_source.md).
- Next papers: [project_paper_ceiling_growth_imaginary.md](project_paper_ceiling_growth_imaginary.md), [project_paper_instrument_circulation.md](project_paper_instrument_circulation.md).
- Journals: [project_journal_strategy.md](project_journal_strategy.md), [reference_rdj4hss.md](reference_rdj4hss.md), [project_gide_conference.md](project_gide_conference.md).
- Biblio: [reference_bib_fulltext_index.md](reference_bib_fulltext_index.md), [reference_cited_works_local_docs_articles.md](reference_cited_works_local_docs_articles.md), [reference_paywalled_acquisition.md](reference_paywalled_acquisition.md), [reference_publist.md](reference_publist.md).
- [HAL SWORD new-version deposit — headers, dotted JEL, password leak trap](reference_hal_sword_update_recipe.md)
- Tooling: OPIDoR DMP import — select "RDA" in the format picker. [feedback_quarto_var_vs_meta.md](feedback_quarto_var_vs_meta.md), [reference_trackchange_review_workflow.md](reference_trackchange_review_workflow.md).

## Harness & telemetry
- [project_imperial_dragon.md](project_imperial_dragon.md), [reference_stats_cache.md](reference_stats_cache.md), [reference_agentic_harness.md](reference_agentic_harness.md), [reference_repo_no_ci.md](reference_repo_no_ci.md).
- [erg update compares a self-committed binary to itself and never advances](project_erg_update_self_reference.md)

## Feedback
- [git check-ignore skips indexed paths, so it proves nothing without --no-index](feedback_check_ignore_needs_no_index.md)
- [A class rule over .gitignore files must be exactly one level deep](feedback_gitignore_class_rule_depth.md)
- [erg close leaves the ticket in tickets/ root — archive it at close time](feedback_erg_close_archive.md)
- [A ticket closed on-branch needs `Ticket: none`, never the archived path](feedback_prclose_onbranch_ticket_none.md)
- [Œconomia prose is History of Economic Thought register, not business-book](feedback_het_register.md)
- [Make commands allowed](feedback_no_long_running.md)
- [A layout refactor is proved by byte-comparing renders, not by a green suite](feedback_render_bitcompare_is_the_gate.md)
- [Phase separation in Makefile](feedback_phase_separation.md)
- [Data flows padme→doudou only](feedback_data_direction.md)
- [No heavy deps for simple tasks](feedback_no_heavy_deps.md)
- [Review agents must use PR branch worktree](feedback_review_agent_worktree.md)
- [Overnight exploration priorities](feedback_overnight_exploration.md)
- [No APC journals](feedback_no_apc.md)
- [User works in parallel](feedback_parallel_work.md)
- [Don't amend commits on open PRs](feedback_no_amend_pr.md)
- [Verify the attributions in an AI-generated include before citing it](feedback_verify_ai_generated_includes.md)
- [Align on the style anchor before showing prose — the author's recurring flags](feedback_letter_voice_flags.md)
- [Always generate PDFs in A4, never US letter](feedback_a4_paper.md)
- [No markdown inside markdown fenced blocks](feedback_no_md_in_md.md)
- [Search parent dirs and /tmp for stale worktrees, not just the worktree list](feedback_worktree_search.md)
- [No --no-verify shortcuts](feedback_no_noverify.md)
- [Commit a branch's own hook fix from the worktree when core.hooksPath is absolute](feedback_worktree_local_hook_commit.md)
- [Decide the branch before editing](feedback_branch_before_edit.md)
- [Always say make corpus, never bare dvc repro](feedback_make_corpus.md)
- [No rebase with DVC symlinks](feedback_no_rebase_dvc.md)
- [Simplest fix first](feedback_simplest_fix.md)
- [SSH doudou→padme works, but PATH must be prepended (uv absent non-interactive)](feedback_ssh_padme.md)
- [Weekend work boundary](feedback_weekend_boundary.md)
- [Verify external sources before advising](feedback_verify_before_advising.md)
- [Drop nulls before pandas merge on DOI](feedback_dropna_before_merge.md)
- [After an ESCALATE verdict, check whether the PR merged anyway](feedback_escalate_check_merge_after_note.md)
- [grep before committing fixes](feedback_grep_before_commit.md)
- [Inspect another ref with show or grep — checkout mutates the working tree](feedback_inspect_ref_readonly.md)
- [Don't oversell break detection](feedback_oversell_breaks.md)
- [Use Tectonic instead of Quarto for next paper](feedback_tectonic_next.md)
- [verify deferral tracker on close](feedback_verify_deferral_tracker.md)
- [For a single-use operation, run the command — don't build a tool around it](feedback_no_tool_for_single_use.md)
- [File editorial decisions beside the submission they decide, as tracked text](feedback_file_decisions_with_submission.md)
- [Cite only numbers tracing to an archived output — live pipeline stats drift](feedback_manuscript_number_provenance.md)
- [A reference enters the manuscript only once read and argued against the core](feedback_read_before_cite.md)
- [Fetch before each sibling merge, then grep-verify the content union](feedback_fetch_before_sibling_merge.md)
- [Sibling merges collide on a shared ticket's Blocked-by bookkeeping](feedback_sibling_close_collides_on_shared_blocker.md)
- [One validation unit per ticket; a number in an instruction is contingent](feedback_atomic_tickets_validation_units.md)
- [Byte-check a refactor old-vs-new on the same data, never against a golden](feedback_bytecheck_old_vs_new_not_golden.md)
- [A size cap forces pruning, never compression to game the number](feedback_caps_force_pruning_not_compression.md)
- [Find the passage that already makes the point before adding prose](feedback_cite_at_existing_locus.md)
- [File the follow-up in the repo that owns the file, not the one that found it](feedback_cross_repo_ticket_in_owning_repo.md)
- [Decide across the whole logical unit; don't half-do it or ask piecemeal](feedback_decide_dont_micromanage.md)
- [A follow-up ticket exists so the parent can close now](feedback_followup_lets_parent_close.md)
- [Don't run the merge gate before the full review fan-out has returned](feedback_gate_after_full_review.md)
- [Cite the evidence when recording an author's decision in a commit or ticket](feedback_hitl_decision_cite_evidence.md)
- [Only a fresh isolated venv proves a package installs](feedback_isolated_venv_proves_installability.md)
- [Never sync the shared env while a sibling agent is mid-run](feedback_no_shared_env_sync_during_sibling_agent.md)
- [Pilot one instance read-only — it can falsify the ticket's design](feedback_pilot_one_instance_critiques_the_ticket.md)
- [Prove a regression pin's teeth by mutating the mechanism it guards](feedback_pin_test_mutation_teeth.md)
- [A PR that files a ticket uses Ticket-ref, never a close claim](feedback_pr_creates_ticket_no_close.md)
- [Write session notes into the tickets they feed — agents start cold](feedback_propagate_notes_to_tickets.md)
- [A green ratchet suite doesn't mean the ceilings match the current manuscript](feedback_ratchet_stale_after_rebuild.md)
- [File the reorg tracker before executing, and keep guards class-level](feedback_reorg_tracker_first_class_guard.md)
- [The arch-rule-9 detector misses contract reads made through a path variable](feedback_rule9_detector_variable_path_blindspot.md)
- [Write a settled debate into the editorial brief, or it gets re-litigated](feedback_settled_debates_to_brief.md)
- [After merging from a worktree, the session stays bound to it and builds stale](feedback_stale_worktree_make.md)
- [Verify no ticket is actively worked before a bulk defer-tag pass](feedback_verify_active_before_defer_tag.md)
- [An isolated agent's prompt must carry worktree-rooted paths](feedback_agent_prompt_worktree_rooted_paths.md)
- [Gate the execute-launch on all scopers returning, not on a quorum](feedback_gate_execute_on_all_scopers.md)
- [Symlink the primary's contract files to validate a data-dependent build](feedback_verify_datadep_worktree_symlink.md)
- [ai-tells.yml is a cross-document guard, not a per-document style choice](feedback_aitells_scope_manuscript_vs_crossdoc.md)
- [Grep the live document before shipping a forbidden-phrase guard](feedback_negative_guard_false_positive_check.md)
- [Verify a Makefile path refactor with make -n and one spot-check, not a build](feedback_verify_makefile_pathrefactor_with_make_n.md)
- [Render and eyeball the PDF — grep and CI miss citation errors](feedback_visual_verify_citations.md)
- [ruff --fix guts re-export facades; probe with a reach-through import](feedback_ruff_fix_breaks_reexport_facades.md)
- [Evicting output to a gitignored dir removes the free directory bootstrap](feedback_evict_to_gitignored_dir_bootstrap.md)
- [Relocating files silently narrows fixed-directory guard globs](feedback_moving_files_narrows_guard_globs.md)
- [N tickets is not an N-wide fan-out — triage for chains and conflicts first](feedback_raid_scope_triage_before_fanout.md)
- [A trivial fix mirroring a reference pattern doesn't need the full protocol](feedback_raid_overkill_for_trivial_reference_pattern_fix.md)
- [Relocating a script here touches eight surfaces, not just the move](project_file_relocation_move_surface.md)
- [An --input gate hides a hardcoded secondary path until the code actually runs](feedback_hardcoded_secondary_path_survives_input_gate.md)
- [A merge gate sees committed artifacts only, never live author authorization](feedback_interactive_authorization_invisible_to_gates.md)
- [Grep the staged primary PDF for the exact claim before citing it](feedback_verify_new_citations_against_primary_pdf.md)
- [Gate the actual branch state, not the PR description text](feedback_gate_verify_branch_not_pr_body.md)
- [A PDF the author fetches by hand lands in ~/Downloads, not the docs tree](feedback_user_pulls_land_in_downloads.md)
- [An independent model gives actionable structural notes on the manuscript](feedback_fable_second_opinion_prose_structure.md)
- [A background session forces worktree and PR even for manuscript prose](feedback_background_session_manuscript_pr_workflow.md)
- [Automate PDF pagination through the LaTeX header, never by hand](feedback_pdf_layout_automate_dont_hand_paginate.md)
- [The rtk-filtered log omits merge commits — verify tips with rev-parse](feedback_rtk_log_hides_merge_commits.md)
- [Join pdftotext output before grepping — line wraps split phrases](feedback_pdftotext_grep_linebreaks.md)
