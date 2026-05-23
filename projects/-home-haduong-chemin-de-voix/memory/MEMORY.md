# Memory index — chemin-de-voix

## Key insights

- The pipeline (raw→extracted→cleaned→training→generation→HITL→manuscript) is now stable and the manuscript is in Draft-1-polished state; the project is editorial-finalization rather than pipeline-building.
- **Empty polish rules = audited clean** (as of 2026-05-16): all 14 voices have been audited; empty rules means nothing actionable found.
- Most tooling failures trace to mismatched names between pipeline stages — prompts, directory names, manifest keys, motif labels across BRIEF/yaml/H1 must stay in sync.
- Corpus maintenance scripts should be idempotent, default to dry-run, and operate per-voice; this pattern (backfill, align, prune) has proven reliable.
- For prose generation in unfamiliar registers/dialects, fan out N≈4 constrained agents (one register each), then synthesize and recommend — single-agent attempts converge on the safest middle. Validated on Aliénor occitan (ticket 0248).
- Project memories go stale faster than feedback memories; retire completed-milestone notes during /dream rather than letting them accumulate.

## Entries

- [N-advisors for register variants](feedback_n_advisors_for_register_variants.md) — fan out ≈4 parallel agents each constrained to one register/dialect/period; save all drafts, recommend one with rationale (proven on 0248 Aliénor occitan)
- [Pandoc DOCX span char styles need custom-style attr](feedback_pandoc_docx_span_styles.md) — `[t]{.cls}` is silently dropped; use `[t]{custom-style="cls"}`; verified by counting `<w:rStyle>` in OOXML
- [LibreOffice headless PDF retirement path](feedback_libreoffice_pdf_path.md) — `soffice --convert-to pdf` handles VN diacritics + italics + monospace; replaces WeasyPrint cleanly when DOCX is source-of-truth
- [merge skill rejects multi-ticket prep PRs](feedback_merge_skill_multi_ticket.md) — raid-prep PRs without a single `Ticket:` line fail erg-pr-merge; use `gh pr merge --squash --delete-branch`; post-merge local checkout error in worktree is cosmetic
- [SOTA parser quirks per model](feedback_sota_parser_quirks_per_model.md) — em-dash/Roman/Strategy D added reactively per new model family; smoke-parse 1–2 samples before fan-out
- [LoRA Qwen3.5-9B échoue vs SOTA + persona — résultat coda](project_lora_negative_result.md) — 0/2502 ors, moy 1.59 vs 3.00 (V4-pro); persona on/off ne change rien; coda-notes.md prêt à réutiliser
- [D4 gap hypothesis refuted (2026-05-18 sweep)](project_d4_gap_refuted.md) — THIN voices mean D4=2.54 vs THICK 2.49; cultural-notes density uncorrelated with D4; 0231 closed without backfill
- [judge lineup locked: Sonnet+Gemini-pro+gpt-5.4-mini](feedback_judge_lineup.md) — 7 smokes × 9 families; Gemini drives Top-1 in 3/7 voices; Kimi/Minimax/Nemotron/Step unusable as judges
- [soft cap: keep ties at rank-5 and rank-6](feedback_soft_cap_aggregation.md) — §4 caps are targets with tie-keeping, not strict slices; doesn't widen output on current data but safety net for corpus-poor voices
- [build_prompt D1/D2 collapsed to D + always cultural](feedback_build_prompt_d_variant.md) — smoke_sota_or.py main() broken post-refactor; use variante="D" + unconditional cultural_path in new scripts
- [background agent worktree locked on timeout](feedback_agent_worktree_locked.md) — branch bare but edits present; work in locked worktree dir directly
- [squash-merge local-master sync via rebase](feedback_squash_merge_sync.md) — use `git rebase origin/master`; absorbed commits skipped automatically, reset --hard blocked by guard hook
- [parallel agent ticket ID collision](feedback_parallel_agent_id_collision.md) — check origin/master ticket IDs before creating batches in a worktree
- [erg Closed: header is valid post-migration](feedback_erg_closed_header.md) — verify-gate wrongly flags Closed: as invalid; Status: is rejected by the validator
- [use @-includes in CLAUDE.md for critical rules](feedback_claudemd_at_include.md) — prose references aren't read by subagents; @file injects content at session start automatically
- [merge skill needs **Ticket:** (bold)](feedback_merge_skill_bold_ticket.md) — plain `Ticket:` is silently skipped; PR merges but ticket stays open
- [per-backend queue beats cycle scheduler](feedback_per_backend_queue_scheduler.md) — for asymmetric workers, shared queue + per-backend pulls; cycle pre-assignment bottlenecks on slow backend
- [gh pr edit fails with Projects-classic GraphQL error](feedback_gh_pr_edit_graphql_fallback.md) — fall back to `gh api PATCH /repos/.../pulls/N`
- [LoRA training use rights for purchased books](feedback_lora_use_rights.md) — user owns all books in voix-*/raw/; local LoRA training does not require additional licensing; TNH EPUBs usable
- [co-authored texts rejected from voice corpora](feedback_coauthored_rejection.md) — mixed-voice signal; mark `rejected: co-authored` in inventory, remove downstream
- [voix-ada corpus is 97% Byron analogue](project_corpus_ada_weighting.md) — Ada's own 44K tokens must be over-represented in training; score threshold behaviour at 0016 split time
- [multilingual corpus strategy](project_multilingual_corpus_strategy.md) — language-fit is tie-breaker only; single-dir layout; HCM Prison Diary is ZH (KMT jail, not VN); translations score auth-1
- [ls vs git log disagreement diagnosis](feedback_ls_vs_git_log_diagnosis.md) — check `git status --short` before assuming "checkout is behind origin"; staged reverts desync working tree from HEAD without touching remote
- [archive.org / Anna's Archive scan-OCR rot pattern](feedback_archive_org_ocr_rot.md) — DjVu/HTML "Full text of"/image-only-PDF sources from archive.org are often OCR-rotted; refetch from Wikisource/Gutenberg/Gallica beats salvaging; bit us 5× this session
- [Bash tool kills background processes with &](feedback_bash_background_sigterm.md) — use run_in_background=true; & inside regular Bash call sends SIGTERM on tool return (exit 143)
- [max_tokens cap for LLM corpus cleaning](feedback_max_tokens_runaway.md) — Qwen3.5-9B enters infinite generation without max_tokens; ~4 tok/s at 65K ctx on A4000
- [celebrate pre-check fails on squash-merge branches](feedback_celebrate_squash_precheck.md) — use `gh pr view --json mergeCommit` + merge-base check instead of HEAD ancestry
- [clean_corpus.py --backends argparse consumes globs](feedback_clean_corpus_backends_argparse.md) — put globs BEFORE --backends, or call clean_corpus.py directly; nargs="+" greedily steals positional args
- [EMPTY threshold false negatives](feedback_empty_threshold_false_negatives.md) — now configurable via --min-ratio (default 0.3); use 0.04 for sutta+commentary or OCR-dense PDFs
- [Héloïse Latin letters on la.wikisource.org](feedback_la_wikisource_heloise.md) — correct page is Scriptor:Heloisa; Epistolae_(Abaelardus) is a citation index, not prose
- [wc -w silent failure on CJK text](feedback_cjk_word_count.md) — returns near-zero for Chinese; use CJK char count + Latin word count × 1.3 instead
- [Edit tool targets main repo, not worktree](feedback_worktree_edit_paths.md) — absolute paths like ~/chemin-de-voix/scripts/foo.py edit main repo; use worktree-rooted paths in worktree sessions
- [/verify simplify lacks isolation — leaks to origin](feedback_verify_simplify_isolation.md) — fetch + check origin after /verify; use cherry-pick not rebase when rebasing sibling branches post-squash
- [rename sweeps must include tests/](feedback_rename_sweep_test_files.md) — grep both scripts/ and tests/ for literal strings before committing; missed test_clean_corpus in PR 87
- [9B cleaning quality gaps](project_9b_cleaning_quality.md) — systematic artifact survival in auteur/manne/hcm/alienor; fix options in ticket 0144 before 0016 sweep
- [unreviewed ≠ clean in polish rules](feedback_unreviewed_not_clean.md) — empty rule list means not yet spot-checked; never infer clean from absence of review
- [model storage in /data/models/](feedback_model_storage.md) — never store model weights in project dirs; use /data/models/ on PADME
- [gemini-3.1-flash-lite truncates large chunks](feedback_gemini_flash_lite_truncation.md) — bodies >30KB output only tail fragment; use ratio check post-run; fallback: llama-3.3-70b-instruct (may add preamble to strip)
- [erg-pr-merge CI-wait false-failure on no-CI repos](feedback_erg_pr_merge_no_ci.md) — gh pr checks --watch never exits if no checks configured; squash-merge already done; verify with gh pr view --json state
- [D seed=42 collapse](feedback_d_seed42_collapse.md) — seed=42 collapses D-notice to 1 translation; use D_SEEDS=[137,271]
- [D token budget 1500](feedback_d_token_budget.md) — D needs 1500 max_new_tokens; 800 truncates 4th/5th translations
- [parse_chunk_headers blank-line bug](feedback_parse_chunk_headers_blank_lines.md) — stopped at first blank line, dropping lang/score; caused 0 training texts for 7+ voices; fix: skip blanks
- [User bio](user_bio.md) — Minh Hà-Duong : né à Paris en 1969, chercheur franco-vietnamien énergie/climat, Paris↔Hanoi
