> **NON-NORMATIVE — measurement record.** The `valid_while` coverage experiment
> run by the fourth review panel over a sample of real memory bodies: what the
> proposed predicate grammar can express, what it can evaluate, and where it is
> the exact truth condition. Cited by
> [the review](./2026-09-10-dragon-memory-design-review-fable-design.md) and by
> §5 of [the design](./2026-09-10-dragon-memory-design.md).

# valid_while ledger — 54 live bodies (57 drawn, 3 `# DELETED` stubs excluded)

Grammar: (a) path exists · (b) pattern present in named file · (c) tool below version.
Categories for NONE: (i) behavioural (ii) owner fact/preference (iii) unconditional incident lesson
(iv) cross-repo/cross-host (v) forge/remote state (vi) path guard / moving path (vii) natural predicate is a NEGATION
(viii) other — dated snapshot, glob not path, version bound unknowable or in the wrong direction.
Flags: CLEAN = predicate is the actual truth condition; PROXY = predicate guards a correlate, not the claim;
UNEVAL = the checkout the predicate names is not at the slug's path on this host (fail-open + lint at scoring).
Types are read from frontmatter, not filename.

## Harness project (projects/-home-haduong--claude/memory) — 20

| # | slug | type | predicate | flag / category |
|---|---|---|---|---|
| 1 | feedback_orphan_branch_may_be_archived_as_a_tag | feedback | NONE | iii; the fact "this repo archives as tags" is remote-ref state (v) |
| 2 | feedback_beat_checkout_model | feedback | (a) `scripts/beat.py` exists ∧ (b) `checkout -B` in it | CLEAN — `scripts/beat.py` is ABSENT today: the predicate would correctly unrank it now |
| 3 | feedback_pgrep_waiter_matches_itself | feedback | NONE | i (pgrep semantics); lesson unconditional |
| 4 | feedback_boolean_probe_must_not_expand_the_value | feedback | NONE | i (bash semantics) |
| 5 | feedback_pipeline_presentation_overlays_raids | feedback | NONE | ii (author directive) |
| 6 | feedback_ancestor_of_main_is_not_current_with_main | feedback | (b) `is-ancestor` in `skills/roar/SKILL.md` | PROXY — the git fact is unconditional; only the "roar uses it" half is guarded |
| 7 | feedback_claude_md_is_thin_loader_idh | feedback | NONE | ii (design decision); `(b) @tickets/AGENTS.md in CLAUDE.md` stays true even if doctrine is added |
| 8 | feedback_raid_worktree_rebase | feedback | NONE | i (worktree snapshot behaviour) |
| 9 | feedback_content_match_recovery_needs_diff_verification | feedback | NONE | iii |
| 10 | feedback_rogue_agent_pattern | feedback | NONE | i (model behaviour); body already carries "root causes fixed by 0216/0228" — a supersedes shape |
| 11 | feedback_cross_repo_tickets_live_at_destination | feedback | NONE | ii/iii |
| 12 | feedback_ab_design_regime_drift | feedback | NONE | iii |
| 13 | feedback_secret_migration_is_credential_audit | feedback | NONE | iii |
| 14 | feedback_dont_pre_close_ticket_in_execution | feedback | NONE | vii — true while `erg-github verify` is ABSENT from `.github/workflows/CI.yml` (confirmed absent today); positive proxy `(a) skills/merge/erg-pr-merge exists` guards the wrong half |
| 15 | user_paper_release_subdir_layout | user | NONE | ii; a path form would name `~/CNRS/papiers/` (vi, cross-host) |
| 16 | user_language | user | NONE | ii |
| 17 | project_harness_repo | project | (b) `shell-init.sh` in `README.md` | PROXY — the systemd timer and `~/.bashrc` line are per-host (iv) |
| 18 | project_idh_gitignore_whitelist_add_f | project | (b) `^\*$` in `.gitignore` | CLEAN |
| 19 | reference_rules_tree_is_resident | reference | NONE | i; version bound runs the wrong way ("since 2.1.266", not "below") (viii) |
| 20 | reference_claude_code_goal_command | reference | NONE | i; form (c) is the intended fit, but the unhiding version is unknowable at write time — any bound written is a guess (viii) |

## git-erg (projects/-home-haduong-git-erg/memory; checkout at `/home/haduong/git-erg` is ABSENT, repo now at `~/CNRS/code/git-erg`, slug not aliased) — 15 live

| # | slug | type | predicate | flag / category |
|---|---|---|---|---|
| 21 | feedback_bundle_related_pr_changes | feedback | NONE | ii/iii |
| 22 | feedback_ticket_file_commit_immediately | feedback | NONE | i (hook cwd reset) |
| 23 | feedback_rebase_large_rename | feedback | NONE | i (git no-op commit) |
| 24 | feedback_scope_audit_git_range | feedback | NONE | i; "raid Phase 7" half would name `skills/raid/SKILL.md` in ANOTHER repo (iv) |
| 25 | feedback_ascii_only_src_go | feedback | (b) `201C` in `tests/test_encoding.sh` | UNEVAL — expressible; checkout not at slug path |
| 26 | feedback_doc_writing_conventions | feedback | NONE | ii |
| 27 | feedback_morning_healthcheck_readonly | feedback | NONE | v (RemoteTrigger state) + dated snapshot "as of 2026-06-05 NO enabled routines" (viii) |
| 28 | feedback_gh_pr_edit_graphql_broken | feedback | NONE | closest to (c) `gh < X`, but X unknown at write and the cause is GitHub-side (v); gh is 2.92.0 today and `rules/git.md` still says broken |
| 29 | feedback_edit_canonical_asset_not_live_copy | **project** (filename says feedback) | (a) `src/go/assets/AGENTS.md` ∧ (b) `go:embed` in `src/go/bootstrap_assets.go` | UNEVAL |
| 30 | project_erg_offline_contract | project | NONE | ii (design contract) |
| 31 | project_release_signing_model | project | (b) `raw/2026-05-30/tickets/erg` in `README.md` | UNEVAL; also SPLIT — the model is durable, the tag line rots; one predicate expires both |
| 32 | reference_rtk_0421_status | reference | (c) `rtk < 0.42.2` | CLEAN — a status-as-of snapshot; rtk is 0.45.0 today so it would correctly unrank. The only (c) hit in the sample |
| 33 | feedback_rebase_check_status_first | feedback | NONE | i; note it CONTRADICTS `rules/git.md` (never stash in a shared checkout) — a supersedes/contradiction case, not a validity one |
| 34 | feedback_merge_auto_boundary_races | feedback | (b) `mergeability` in `~/.claude/skills/merge/erg-pr-merge` | iv, harness-directed — evaluable because the scorer lives in the harness; names a `~/` path (vi) |
| 35 | feedback_process_doc_ticket_id_rot | feedback | NONE | iii |

## AEDIST paper (projects/-home-haduong-CNRS-papiers-actif-AEDIST-technical-report/memory; the dir at that path holds two dated folders and no repo) — 15

| # | slug | type | predicate | flag / category |
|---|---|---|---|---|
| 36 | feedback_build_from_user_worktree | feedback | NONE | iii |
| 37 | feedback_local_vs_cloud | feedback | NONE | ii (research design) |
| 38 | feedback_gaze_fork_dies_in_background_jobs | feedback | NONE | vii + iv — true until gaze awaits reviewers when forked; the fix lands in another repo |
| 39 | feedback_pagination_widow_verification | feedback | NONE | iii |
| 40 | feedback_haiku_truncated_final_reports | feedback | NONE | i (model behaviour) |
| 41 | feedback_autonomous_means_execute | feedback | NONE | ii |
| 42 | feedback_editorial_book_work | feedback | NONE | ii |
| 43 | feedback_bg_merge_anchoring | feedback | (b) `-C` in `~/.claude/skills/merge/erg-pr-merge` | iv harness-directed, evaluable; `~/` path (vi) |
| 44 | feedback_make_not_loops | feedback | NONE | ii |
| 45 | feedback_no_invented_names | feedback | NONE | ii (author rule); `(a) tests/test_reference_integrity.py` would be a proxy |
| 46 | reference_autonomous_padme | reference | NONE | iv cross-host (padme) — the TTL table's "remote machine config, 90 days" row; valid_while cannot replace it |
| 47 | project_structured_dirs_registry | project | (b) `STRUCTURED_DIRS` in `experiments/Makefile` | UNEVAL — file not reachable from the slug path today |
| 48 | project_sweep2_results | project | NONE | viii dated result, superseded by later sweeps — a `supersedes` case |
| 49 | project_model_registry_consolidation | project | (a) `experiments/models.yaml` exists | UNEVAL; the other half is a NEGATION ("no `sweeps/` directory") (vii) |
| 50 | project_exp1_design_decisions | project | NONE | viii — "valid while ticket 0175 is open" needs a glob `tickets/0175-*.erg`, and "open" is the negation of `closed/` |

## Harness tier (memory/) — 4

| # | slug | type | predicate | flag / category |
|---|---|---|---|---|
| 51 | feedback_subagent_model_effort_levers | feedback | NONE | i; "measured on 2.1.267" is a lower bound, wrong direction for (c) (viii) |
| 52 | reference_branch_cleanup_incidents | reference | (b) `is-ancestor` in `rules/git.md` ∧ (a) `tests/test_branch_cleanup_recipes.py` | CLEAN |
| 53 | reference_git_in_a_worktree_session | reference | (a) `scripts/pretooluse-worktree-path-guard.sh` exists | PROXY — guards existence, not the two-refusal behaviour the note is about |
| 54 | reference_zotero | reference | NONE | ii (account facts) + v (API behaviour) |

## Tally

| stratum | n | expressible (any) | evaluable today | CLEAN |
|---|---|---|---|---|
| harness project | 20 | 4 (#2 #6 #17 #18) | 4 | 2 |
| git-erg | 15 | 5 (#25 #29 #31 #32 #34) | 2 (#32 #34) | 1 |
| AEDIST | 15 | 3 (#43 #47 #49) | 1 (#43) | 0 |
| harness tier | 4 | 2 (#52 #53) | 2 | 1 |
| **total** | **54** | **14 (26%)** | **9 (17%)** | **4 (7%)** |

By type: feedback 5/36 (14%) · user 0/2 · project 6/9 (67%) · reference 3/7 (43%).

NONE categories (40): i=13 · ii=13 · iii=8 · iv=1 · v=1 · vii=2 · viii=2 (several rows carry two; primary counted).

## Corpus-wide probes (966 live bodies)

- Version strings pinned anywhere: 9 bodies (2.1.267 ×3, 2.1.266 ×2, 2.1.232, 2.1.169, rtk 0.42.1, rtk 0.34.3, Go 1.19). Most are lower bounds ("measured on", "since").
- Tool versions knowable at scoring: `claude` 2.1.267, `rtk` 0.45.0, `gh` 2.92.0, tectonic, latexmk, python3. **`erg version` prints sha256/built/revision and no version number** — form (c) cannot name it.
- Negation-shaped conditions (until fixed / RESOLVED by / superseded by): 20 bodies.
- Bodies naming a `/home/haduong` or `~/` path: 163 — `check-agnostic.sh` scans `projects/` too, so a `(b)` predicate on a `~/` file would be flagged by the harness's own guard.
- Forge-state truths (deleteBranchOnMerge, branch protection, squash, GraphQL): 44 bodies.
- Existing `supersedes`/`valid_while`/`expires` fields: 0.
