# Memory index — chemin-de-voix

## Key insights

- The pipeline (raw→extracted→cleaned→training→generation→HITL→manuscript) is now stable and the manuscript is in Draft-1-polished state; the project is editorial-finalization rather than pipeline-building.
- **Empty polish rules = audited clean** (as of 2026-05-16): all 14 voices have been audited; empty rules means nothing actionable found.
- Most tooling failures trace to mismatched names between pipeline stages — prompts, directory names, manifest keys, motif labels across BRIEF/yaml/H1 must stay in sync.
- Corpus maintenance scripts should be idempotent, default to dry-run, and operate per-voice; this pattern (backfill, align, prune) has proven reliable.
- For prose generation in unfamiliar registers/dialects, fan out N≈4 constrained agents (one register each), then synthesize and recommend — single-agent attempts converge on the safest middle. Validated on Aliénor occitan (ticket 0248).
- Project memories go stale faster than feedback memories; retire completed-milestone notes during /dream rather than letting them accumulate.

## Entries

- [N-advisors for register variants](feedback_n_advisors_for_register_variants.md)
- [Pandoc DOCX span char styles need custom-style attr](feedback_pandoc_docx_span_styles.md)
- [LibreOffice headless PDF retirement path](feedback_libreoffice_pdf_path.md)
- [merge skill rejects multi-ticket prep PRs](feedback_merge_skill_multi_ticket.md)
- [SOTA parser quirks per model](feedback_sota_parser_quirks_per_model.md)
- [LoRA Qwen3.5-9B échoue vs SOTA + persona — résultat coda](project_lora_negative_result.md)
- [D4 gap hypothesis refuted (2026-05-18 sweep)](project_d4_gap_refuted.md)
- [judge lineup locked: Sonnet+Gemini-pro+gpt-5.4-mini](feedback_judge_lineup.md)
- [soft cap: keep ties at rank-5 and rank-6](feedback_soft_cap_aggregation.md)
- [build_prompt D1/D2 collapsed to D + always cultural](feedback_build_prompt_d_variant.md)
- [background agent worktree locked on timeout](feedback_agent_worktree_locked.md)
- [squash-merge local-master sync via rebase](feedback_squash_merge_sync.md)
- [parallel agent ticket ID collision](feedback_parallel_agent_id_collision.md)
- [erg Closed: header is valid post-migration](feedback_erg_closed_header.md)
- [use @-includes in CLAUDE.md for critical rules](feedback_claudemd_at_include.md)
- [merge skill needs **Ticket:** (bold)](feedback_merge_skill_bold_ticket.md)
- [per-backend queue beats cycle scheduler](feedback_per_backend_queue_scheduler.md)
- [gh pr edit fails with Projects-classic GraphQL error](feedback_gh_pr_edit_graphql_fallback.md)
- [LoRA training use rights for purchased books](feedback_lora_use_rights.md)
- [co-authored texts rejected from voice corpora](feedback_coauthored_rejection.md)
- [voix-ada corpus is 97% Byron analogue](project_corpus_ada_weighting.md)
- [multilingual corpus strategy](project_multilingual_corpus_strategy.md)
- [ls vs git log disagreement diagnosis](feedback_ls_vs_git_log_diagnosis.md)
- [archive.org / Anna's Archive scan-OCR rot pattern](feedback_archive_org_ocr_rot.md)
- [Bash tool kills background processes with &](feedback_bash_background_sigterm.md)
- [max_tokens cap for LLM corpus cleaning](feedback_max_tokens_runaway.md)
- [celebrate pre-check fails on squash-merge branches](feedback_celebrate_squash_precheck.md)
- [clean_corpus.py --backends argparse consumes globs](feedback_clean_corpus_backends_argparse.md)
- [EMPTY threshold false negatives](feedback_empty_threshold_false_negatives.md)
- [Héloïse Latin letters on la.wikisource.org](feedback_la_wikisource_heloise.md)
- [wc -w silent failure on CJK text](feedback_cjk_word_count.md)
- [Edit tool targets main repo, not worktree](feedback_worktree_edit_paths.md)
- [/verify simplify lacks isolation — leaks to origin](feedback_verify_simplify_isolation.md)
- [rename sweeps must include tests/](feedback_rename_sweep_test_files.md)
- [9B cleaning quality gaps](project_9b_cleaning_quality.md)
- [unreviewed ≠ clean in polish rules](feedback_unreviewed_not_clean.md)
- [model storage in /data/models/](feedback_model_storage.md)
- [gemini-3.1-flash-lite truncates large chunks](feedback_gemini_flash_lite_truncation.md)
- [erg-pr-merge CI-wait false-failure on no-CI repos](feedback_erg_pr_merge_no_ci.md)
- [D seed=42 collapse](feedback_d_seed42_collapse.md)
- [D token budget 1500](feedback_d_token_budget.md)
- [parse_chunk_headers blank-line bug](feedback_parse_chunk_headers_blank_lines.md)
- [User bio](user_bio.md)
