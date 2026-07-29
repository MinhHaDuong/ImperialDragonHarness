## Key insights

- The corpus pipeline degrades silently at several joints (relevance flag skipped without torch, GROBID down, stale Feather caches): a headline number that moves between passes is the alarm — verify the producing stage before citing any count.
- Author workflow: batch the decisions, execute autonomously to PRs; manuscript prose changes always return to the author for arbitration, and agent cut plans start with whole-passage removal, never condensation-only.
- Environment values shadow: ambient shell exports beat `--env-file`, and secrets belong in the harness env, never the project `.env`.
- Paywall/bot walls (oecd.org, one.oecd.org) yield to the author's own browser session via cookie replay; dead institutional series resurrect through Wayback and treaty-body mirrors (CBD, ReliefWeb).
- Numbers in prose must be vars-driven from the pipeline; hand-typed figures rot at every corpus rebuild (28%→24%, 27%/47% gradient inversion).

## Entries

- [PR scope discipline](feedback_scope_discipline.md) — don't add arch rules/tickets/sweeps to a feature PR branch
- [Lean over comprehensive](feedback_lean_methods.md) — prefer one right method per concern, shed sunk-cost bias on existing code
- [Verify contract](feedback_verify_contract.md) — /verify loop for PR gating; anti-rubber-stamp; two rounds max; never merges from skill
- [Agent timeout on refactor](feedback_agent_timeout_refactor.md) — provide pre-written code, narrow scope, commit early
- [Reimagine catches stale deps](feedback_reimagine_catches_stale_deps.md) — always reimagine before execution; dep graphs decay fast
- [Pass full DF not a slice to stat helpers](feedback_null_df_slicing.md) — sliced DataFrame silently produces NaN output; callee needs all columns
- [Companion paper design](project_companion_paper_design.md) — DORMANT (author 2026-07-23: no third paper); outlets = data paper + Œconomia only
- [Verify vars file provenance](feedback_vars_file_provenance.md) — check compute_vars.py + Makefile before editing metadata-files; stale artifacts mislead
- [Machine: padme](reference_machine_padme.md) — GPU server; corpus data lives here; test_corpus_acceptance failures are real, not expected
- [a4paper always](feedback_a4paper.md) — every QMD format:pdf: block must have papersize: a4
- [Analytical null as overlay](feedback_analytical_null_overlay.md) — MC + analytical ribbons as overlapping semi-transparent fills; no standalone script
- [Verify agent must cd into PR worktree](feedback_verify_agent_worktree.md) — tests run outside the PR worktree produce false failures; always cd in first
- [Never force-delete active worktrees](feedback_worktree_deletion.md) — unlocked ≠ abandoned; check for other sessions before --force remove
- [gh Projects-classic error](feedback_gh_projects_classic_error.md) — gh pr edit/merge exit non-zero on a deprecated-Projects GraphQL error; use gh api REST + gh pr ready
- [Auto-discovery class guards](feedback_autodiscovery_class_guard.md) — Makefile/source-driven discovery beats hardcoded lists; caught 5 missed/rebased-in offenders
- [Resolve all conflict hunks, validate before push](feedback_merge_conflict_all_hunks.md) — first-match regex left raw markers on main; union wrong for removed headers
- [padme Downloads dir](reference_padme_downloads_dir.md) — ~/Téléchargements until locale fix; use xdg-user-dir DOWNLOAD
- [Rio-markers dataset for book](reference_riomarkers_dataset_book.md) — DSD_RIOMRKR@DF_RIOMARKERS zips in data/book/riomarkers/; book chapter, NOT the data paper
- [Téléchargements is scratch](feedback_telechargements_scratch.md) — move+checksum+delete downloads to durable homes asap
- [Cookie-replay fetch](reference_cookie_replay_fetch.md) — author's Firefox cookies unlock oecd.org/one.oecd.org; tabs via recovery.jsonlz4
- [uv --env-file no override](feedback_env_file_no_override.md) — ambient shell vars shadow refreshed .env keys; pass rotated creds explicitly
- [Pipe masks exit code](feedback_pipe_masks_exit_code.md) — `cmd | tail` in a background task reports exit 0 on failure; run bare or pipefail
