# Memory Index

## Key insights

- **Isolation is the core discipline.** One ticket, one worktree, one PR — no cross-contamination. Branch existence is the claim; no external state tags needed.
- **Empirical verification before belief.** Verify ticket premises before implementing; verify agent claims (confabulated precedents, remote agents' sandbox-specific failures) with a cheap local check; verify fork output actually answers the request before consuming it; verify the delivery gate (CI, hook) actually runs a check before claiming the exit criterion met.
- **Negative controls must prove the property they claim.** Vacuous passes hide behind green checkmarks — a path-only snapshot "detecting overwrites", a control depending on a git-template artifact. Red-step TDD (prove the control fails first) is the antidote.
- **Guards beat prose.** Every invariant that mattered got mechanized (docs drift, CMDS coverage, scope confinement); prose-only contracts rot. The merge pipeline matured the same way: the script now self-recovers from GitHub races — the remaining traps are human shortcuts.
- **One canonical source, no copies.** Edit `src/go/assets/` not the deployed copy; rebase against `origin/main` not local main; the traveling binary converges by PR from one reference blob.

## Entries

- [gh pr edit GraphQL broken](feedback_gh_pr_edit_graphql_broken.md)
- [rtk 0.42.1 status](reference_rtk_0421_status.md)
- [morning healthcheck disabled](feedback_morning_healthcheck_readonly.md)
- [remote sandbox test claims](feedback_remote_sandbox_test_claims.md)
- [verify fork misfire](feedback_verify_fork_misfire.md)
- [raid branch as annotation carrier](feedback_raid_branch_annotation_carrier.md)
- [verify gate requires ticket reference](feedback_verify_gate_ticket_ref.md)
- [erg offline contract](project_erg_offline_contract.md)
- [scope audit must use two-dot git range](feedback_scope_audit_git_range.md)
- [llama-server workload on padme](project_llama_server_workload.md)
- [doc writing conventions](feedback_doc_writing_conventions.md)
- [branch as claim, no claimed tag](feedback_branch_as_claim.md)
- [complexity guards are defense-in-depth](feedback_complexity_guard_defense_in_depth.md)
- [Blocked-by parent breaks merge](feedback_blockedby_parent_breaks_merge.md)
- [no CI callback wait](feedback_no_ci_callback_wait.md)
- [one worktree per ticket](feedback_one_worktree_per_ticket.md)
- [renames are hard, not aliased](feedback_rename_hard_not_aliased.md)
- [edit canonical asset not live copy](feedback_edit_canonical_asset_not_live_copy.md)
- [bundle follow-up tickets](feedback_bundle_followup_tickets.md)
- [bundle related PR changes](feedback_bundle_related_pr_changes.md)
- [rebase fails silently after large rename](feedback_rebase_large_rename.md)
- [simplify fixes may not reach PR branch](feedback_simplify_commit_not_pushed.md)
- [always rebase before merge](feedback_rebase_before_merge.md)
- [YubiKey GPG setup pitfalls](feedback_yubikey_gpg_setup.md)
- [no direct push to main](feedback_no_direct_push_main.md)
- [release signing model](project_release_signing_model.md)
- [verify premises before code](feedback_verify_premises_before_code.md)
- [ASCII-only src/go/](feedback_ascii_only_src_go.md)
- [stale duplicate tickets](feedback_stale_duplicate_tickets.md)
- [rebase check status first](feedback_rebase_check_status_first.md)
- [UX dry-run pattern](feedback_ux_dryrun_pattern.md)
- [process doc ticket-ID rot](feedback_process_doc_ticket_id_rot.md)
- [ticket file commit immediately](feedback_ticket_file_commit_immediately.md)
- [rebase from local main contaminates branch](feedback_rebase_contaminates_from_local_main.md)
- [values: excellence, integrity, bienveillance](feedback_values_excellence_integrity_bienveillance.md)
- [verify pushes fixes to branch](feedback_verify_pushes_fixes.md)
- [full violation list before PASS claim](feedback_full_violation_list_before_pass_claim.md)
- [post-rebase domain revalidate](feedback_post_rebase_domain_revalidate.md)
- [merge --auto boundary races](feedback_merge_auto_boundary_races.md)
- [idempotency: byte not count](feedback_idempotency_byte_not_count.md)
- [gofmt smart-quotes vs ASCII](feedback_gofmt_smartquotes_vs_ascii.md)
- [ticket store map](reference_ticket_store_map.md)
- [cross-session worktree hijack](feedback_cross_session_worktree_hijack.md)
- [meta-test: owner pays](feedback_meta_test_owner_pays.md)
- [Workflow sandbox contract](feedback_workflow_sandbox_contract.md)
- [red-control: no cooperating instrumentation](feedback_redcontrol_no_cooperating_instrumentation.md)
- [verify delivery gate runs check](feedback_verify_delivery_gate_runs_check.md)
- [sweep emitted vs gated surface](feedback_sweep_emitted_vs_gated_surface.md)
