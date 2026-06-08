# Memory Index

## Key insights

- **Isolation is the core discipline.** One ticket, one worktree, one PR — no cross-contamination. Branch existence is the claim; no external state tags needed.
- **Empirical verification before belief.** Verify ticket premises before implementing; verify agent claims (confabulated precedents, remote agents' sandbox-specific failures) with a cheap local check; verify fork output actually answers the request before consuming it; verify the delivery gate (CI, hook) actually runs a check before claiming the exit criterion met.
- **Negative controls must prove the property they claim.** Vacuous passes hide behind green checkmarks — a path-only snapshot "detecting overwrites", a control depending on a git-template artifact. Red-step TDD (prove the control fails first) is the antidote.
- **Guards beat prose.** Every invariant that mattered got mechanized (docs drift, CMDS coverage, scope confinement); prose-only contracts rot. The merge pipeline matured the same way: the script now self-recovers from GitHub races — the remaining traps are human shortcuts.
- **One canonical source, no copies.** Edit `src/go/assets/` not the deployed copy; rebase against `origin/main` not local main; the traveling binary converges by PR from one reference blob.

## Entries

- [gh pr edit GraphQL broken](feedback_gh_pr_edit_graphql_broken.md) — gh pr edit dies on projectCards deprecation; PATCH PR bodies via gh api REST instead
- [rtk 0.42.1 status](reference_rtk_0421_status.md) — updated 2026-06-05: wc-l-returns-0 FIXED; bare `gh pr checks` still needs PR number; compound find still rejected; erg-check truncation unverified
- [morning healthcheck disabled](feedback_morning_healthcheck_readonly.md) — the daily 4-repo routine was judged useless and disabled 2026-06-05; do not re-enable; zero enabled remote routines remain
- [remote sandbox test claims](feedback_remote_sandbox_test_claims.md) — cloud routine agents can't `git worktree add` (exit 128) and misreport sandbox failures as "pre-existing on main"; re-run the test locally before believing
- [verify fork misfire](feedback_verify_fork_misfire.md) — a forked /verify can re-run the previous skill's task; sanity-check fork output answers the request, retry with a self-describing args string
- [raid branch as annotation carrier](feedback_raid_branch_annotation_carrier.md) — push raid branch; execute agents import annotated tickets via fetch + checkout FETCH_HEAD; 5/5 clean in raid 219-224
- [verify gate requires ticket reference](feedback_verify_gate_ticket_ref.md) — add `**Ticket:** tickets/<name>.erg` to PR body before opening; /verify fails at phase 1 without it
- [erg offline contract](project_erg_offline_contract.md) — erg must work offline in isolated VMs; network resolution is opt-in via --resolve, not the default
- [scope audit must use two-dot git range](feedback_scope_audit_git_range.md) — raid Phase 7: use `git log base..branch`, never `base...branch`, or you mistake parallel main commits for PR scope creep
- [llama-server workload on padme](project_llama_server_workload.md) — two instances run unattended OCR cleaning on Qwen3.5-9B; do not restart, benchmark, or hit endpoints
- [doc writing conventions](feedback_doc_writing_conventions.md) — PEP prose marked GENERATED for human review; spec is agent-first; align code literally on spec
- [branch as claim, no claimed tag](feedback_branch_as_claim.md) — no claimed/pending tag; branch existence is the claim signal; external state stays out of ticket headers
- [complexity guards are defense-in-depth](feedback_complexity_guard_defense_in_depth.md) — fast/O(N²) guards are layered by design; don't redesign toward a bulletproof detector; assert TotalAlloc not Mallocs; ReadMemStats is blind to subprocesses
- [Blocked-by parent breaks merge](feedback_blockedby_parent_breaks_merge.md) — never put Blocked-by:<parent> on a child ticket; erg-pr-merge's per-file pre-commit validate can't resolve it and aborts the merge mid-flight
- [no CI callback wait](feedback_no_ci_callback_wait.md) — don't arm background waiters/Monitors for GitHub CI; they time out or fire stale; let /merge's --watch block, or check gh pr checks inline when needed
- [one worktree per ticket](feedback_one_worktree_per_ticket.md) — new bug mid-task → file a ticket and stop; never implement a second bug's fix in the current ticket's worktree/branch; isolation is paramount
- [renames are hard, not aliased](feedback_rename_hard_not_aliased.md) — erg header/command renames hard-reject old form with "run erg migrate" hint; no deprecated aliases (no precedent in codebase)
- [edit canonical asset not live copy](feedback_edit_canonical_asset_not_live_copy.md) — git-erg only: change erg agent docs in src/go/assets/ (embedded, propagating), not the diverged tickets/ copy; let CI rebuild the binary, don't rebuild/reinstall locally
- [bundle follow-up tickets](feedback_bundle_followup_tickets.md) — raid/review follow-ups: commit the ticket file onto the spawning PR branch (not main); ticket only, not the fix
- [bundle related PR changes](feedback_bundle_related_pr_changes.md) — apply a guidance change to its own artifacts in the SAME PR; don't spawn a follow-up PR for the same theme; never place an artifact violating a convention you're introducing that session
- [rebase fails silently after large rename](feedback_rebase_large_rename.md) — when a large rename lands mid-wave, cherry-pick onto fresh main; rebasing old branch produces same-tree no-op and PR stays CONFLICTING
- [simplify fixes may not reach PR branch](feedback_simplify_commit_not_pushed.md) — after /verify reports simplify fixes, confirm with `git log origin/<branch>` before merging; throwaway worktrees may not push
- [always rebase before merge](feedback_rebase_before_merge.md) — rebase onto current origin/main, push --force-with-lease, wait for CI, then /merge; prevents "Base branch was modified" mid-merge failures
- [YubiKey GPG setup pitfalls](feedback_yubikey_gpg_setup.md) — install scdaemon first; answer n to off-card backup or key write partially fails; key 4A46C91E03B83B23 on serial 36002329
- [no direct push to main](feedback_no_direct_push_main.md) — everything through a PR, even ticket lifecycle files; workflow.md exception is aspirational but permission model doesn't support it
- [release signing model](project_release_signing_model.md) — sign tags at release cadence not CI cadence; curl pins to tag name not main; current tag: 2026-05-30
- [verify premises before code](feedback_verify_premises_before_code.md) — empirically test a ticket's stated premise before implementing; two raids saved by catching false observations first
- [ASCII-only src/go/](feedback_ascii_only_src_go.md) — src/go ASCII-only EXCEPT *.go may hold U+201C/U+201D (gofmt smart quotes, ticket 0217); assets strict; em-dashes still fail (ticket 0167)
- [stale duplicate tickets](feedback_stale_duplicate_tickets.md) — long-running PRs with close-and-archive commits reintroduce open copies of archived tickets; run erg check before merge; 0198 adds the canary test
- [rebase check status first](feedback_rebase_check_status_first.md) — check `git status` before rebasing; dirty tracked files abort with conflict; stash first, rebase, pop
- [UX dry-run pattern](feedback_ux_dryrun_pattern.md) — cold-prompt agent with Transcript/Friction log/Summary format; tickets created outside worktree are invisible to git add
- [process doc ticket-ID rot](feedback_process_doc_ticket_id_rot.md) — don't embed ticket IDs in operational steps of process docs; tickets close but docs live; the run-log is the durable record
- [ticket file commit immediately](feedback_ticket_file_commit_immediately.md) — untracked ticket files strand on branch switches; commit immediately or embed content in execute agent prompt
- [rebase from local main contaminates branch](feedback_rebase_contaminates_from_local_main.md) — always rebase against origin/main; local main may have unpushed agent commits that silently sneak into the rebase
- [values: excellence, integrity, bienveillance](feedback_values_excellence_integrity_bienveillance.md) — the author's three guiding values; integrity & safety outrank speed; use expert councils for forks
- [verify pushes fixes to branch](feedback_verify_pushes_fixes.md) — /verify may commit+push fixes from its review worktree; fetch + ff-only your local branch before merge or a rebase drops them
- [full violation list before PASS claim](feedback_full_violation_list_before_pass_claim.md) — rtk truncates erg check output to the last violation; use erg validate FILES or redirect+grep -c before claiming PASS anywhere
- [post-rebase domain revalidate](feedback_post_rebase_domain_revalidate.md) — conflict-free rebase silently dropped a migration hunk upstream had touched; re-run erg check / make check-fast after every rebase before push
- [merge --auto boundary races](feedback_merge_auto_boundary_races.md) — post-close recompute race FIXED (IDH 0200 closed; script self-recovers, 3/3 on 2026-06-05); residual trap: direct-merging a PRE-close bounce skips the ticket close — re-run the script instead, verify ticket state after any direct merge
- [idempotency: byte not count](feedback_idempotency_byte_not_count.md) — test in-place editors by byte-comparing reruns; marker-count tests miss blank-line accumulation
- [gofmt smart-quotes vs ASCII](feedback_gofmt_smartquotes_vs_ascii.md) — gofmt's STOCK smart-quotes (`''`->U+201D, Go 1.19+), NOT a broken/padme toolchain (I wrongly said so); RESOLVED in 0217: policy allows U+201C/U+201D in *.go + gofmt/vet ratchet; gofmt -w is now safe
- [ticket store map](reference_ticket_store_map.md) — padme host config → ~/padme/tickets; IDH harness → ~/.claude/tickets; erg tool → ~/git-erg; classify by what it fixes
- [cross-session worktree hijack](feedback_cross_session_worktree_hijack.md) — assert `git branch --show-current` before mutating git in a finished agent worktree; another session may have re-pointed it
- [meta-test: owner pays](feedback_meta_test_owner_pays.md) — coverage meta-tests fail on whichever PR is in flight when a parallel key lands; add the fixture in your PR, never an exemption
- [Workflow sandbox contract](feedback_workflow_sandbox_contract.md) — no process global; args may arrive stringified; schemas must tolerate stringified ints; decorative agents degrade not die; resume needs byte-identical CONFIG
- [red-control: no cooperating instrumentation](feedback_redcontrol_no_cooperating_instrumentation.md) — mutate the defect only, never the counter; a guard whose signal lives inside the mutable region can be orphaned by the defect it watches (0240/gaze r1)
- [verify delivery gate runs check](feedback_verify_delivery_gate_runs_check.md) — "gate G now catches Y" exit criteria: read G's actual config (CI yml, hook) for the line invoking the check; a green local make check doesn't prove the server-side gate runs it (0241/advisor)
