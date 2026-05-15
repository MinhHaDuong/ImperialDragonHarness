# Memory index — chemin-de-voix

## Key insights

- The pipeline is now stable (raw→extracted→cleaned→training) but cleaning quality has known systematic gaps: the local 9B fails on domain-specific artifacts not covered by its prompt (verse numbers, running headers, signature fragments).
- Most tooling failures trace to mismatched names between pipeline stages — prompts, directory names, and manifest keys must stay in sync as the pipeline evolves.
- Corpus maintenance scripts should be idempotent, default to dry-run, and operate per-voice; this pattern (backfill, align, prune) has proven reliable.
- The two-GPU async cleaning setup handles bulk passes well; targeted re-cleaning of specific sources is better served by an API model (OpenRouter) than spinning up local GPUs.
- Resolved one-time source issues (OCR remediation, Héloïse fetch) should be retired from memory once confirmed closed — project memories go stale faster than feedback memories.

## Entries

- [squash-merge local-master sync via rebase](feedback_squash_merge_sync.md) — use `git rebase origin/master`; absorbed commits skipped automatically, reset --hard blocked by guard hook
- [parallel agent ticket ID collision](feedback_parallel_agent_id_collision.md) — check origin/master ticket IDs before creating batches in a worktree
- [erg Closed: header is valid post-migration](feedback_erg_closed_header.md) — verify-gate wrongly flags Closed: as invalid; Status: is rejected by the validator
- [use @-includes in CLAUDE.md for critical rules](feedback_claudemd_at_include.md) — prose references aren't read by subagents; @file injects content at session start automatically
- [merge skill needs **Ticket:** (bold)](feedback_merge_skill_bold_ticket.md) — plain `Ticket:` is silently skipped; PR merges but ticket stays open
- [per-backend queue beats cycle scheduler](feedback_per_backend_queue_scheduler.md) — for asymmetric workers, shared queue + per-backend pulls; cycle pre-assignment bottlenecks on slow backend
- [gh pr edit fails with Projects-classic GraphQL error](feedback_gh_pr_edit_graphql_fallback.md) — fall back to `gh api PATCH /repos/.../pulls/N`
- [LoRA training use rights for purchased books](feedback_lora_use_rights.md) — user owns all books in voix-*/raw/; local LoRA training does not require additional licensing; TNH EPUBs usable
- [co-authored texts rejected from voice corpora](feedback_coauthored_rejection.md) — mixed-voice signal; mark `rejected: co-authored` in inventory, remove downstream
- [ticket 0015 pilot status](project_0015_status.md) — 9B operational on PADME; corpus cleaned but has known quality gaps (ticket 0144); fix before 0016 sweep
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
- [milestone 1 fetch phase done](project_milestone1_done.md) — all 14 voices ≥ 100K tokens (2026-05-14); Galle stele added; next: 0015 pipeline pilot
- [Edit tool targets main repo, not worktree](feedback_worktree_edit_paths.md) — absolute paths like ~/chemin-de-voix/scripts/foo.py edit main repo; use worktree-rooted paths in worktree sessions
- [/verify simplify lacks isolation — leaks to origin](feedback_verify_simplify_isolation.md) — fetch + check origin after /verify; use cherry-pick not rebase when rebasing sibling branches post-squash
- [rename sweeps must include tests/](feedback_rename_sweep_test_files.md) — grep both scripts/ and tests/ for literal strings before committing; missed test_clean_corpus in PR 87
- [9B cleaning quality gaps](project_9b_cleaning_quality.md) — systematic artifact survival in auteur/manne/hcm/alienor; fix options in ticket 0144 before 0016 sweep
