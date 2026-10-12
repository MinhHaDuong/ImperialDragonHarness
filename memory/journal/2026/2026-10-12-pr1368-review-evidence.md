# PR1368 review evidence and local CI events

Project: ImperialDragonHarness. Public audience: this entry contains published PR/code information, review outcomes and sanitized runtime identity facts, with no credentials or private infrastructure details.

The writer created the no-workflow preflight fix as Codex. Its production-session turn_context after 2026-10-12T07:51:26Z reports model_provider=openai, model=gpt-6-luna and effort=medium; the implementation and documentation commits occurred after that event. No explicit model-version field was exposed.

Codex child session_meta and turn_context establish actual provider=openai, model=gpt-6.1-sol and effort=medium for pr1368_correctness, pr1368_consistency, pr1368_scope, pr1368_redteam and pr1368_docprop. No explicit model-version field was exposed. Some inherited contexts precede each child's own gpt-6.1-sol turn; identities below follow the child's own turn rather than the inherited context.

The initial manifest named claude-sonnet-5-5 for Red Team, but the launched pr1368_redteam context actually ran gpt-6.1-sol. A separate Claude Code process later reviewed the final published diff with tools disabled. Its requested model was claude-sonnet-5-5 with medium effort, and its JSON modelUsage reports canonicalModel=claude-sonnet-5-5, provider=firstParty and total_cost_usd=0.29034. No provider revision was exposed. The first attempt to launch that process was rejected before execution by automatic approval review on a private-payload claim; the GitHub repository API returned visibility=public and private=false, and the evidence-backed retry ran successfully.

The scope seat's first attempt at 3734816f969c1a4bcf82e2396872087ec8b36243 stopped on a failed forge-anchor lookup and returned comment. The same scope context later verified 4126c263034384a46e162599829afeb977cfab8e with elevated forge access and approved.

Consistency's ticket-context finding was adopted in 4126c263034384a46e162599829afeb977cfab8e. Documentation propagation's trace-header wording observation was adopted in 03963c9f135c06efefb7e562f2177d96589de1d9. Other seats found no blocking implementation issue. The cross-family seat's optional invalid-HEAD classification and test-wording/assertion suggestions were not adopted: invalid-HEAD classification predates this change and remains nonzero, while the focused regression assertions already cover the requested two outcomes.

Local validation: make check-fast 962 passed; make lint 182 passed; final focused regression tests 2 passed. The complete local CI on padme ran the unchanged code at 03963c9f135c06efefb7e562f2177d96589de1d9: ten jobs passed, zero failed, zero skipped; its pytest job reported 1554 passed and 12 skipped. Subsequent b862f75c79fa40a4a92d8a07d1fd14e3347a7389 changed only ticket closure/exit criteria. GitHub required checks passed and PR1368 merged at 2026-10-12T08:32:35Z with integration commit f0716cf319634dacc6c1d62964dbea6010c021df.

Durable forge trail: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1368 . The review at 03963c9 recorded initial findings/resolutions; a second review at the same head recorded the cross-family approval and its non-adopted comments.

## Raw final report: correctness

# Correctness review — PR #1368

Anchor: `3734816f969c1a4bcf82e2396872087ec8b36243`, compared with `origin/main`. HEAD and the three-file roster match the assigned review.

Findings: none. Confidence: high.

The committed-workflow probe now precedes access to `ci-local/common.sh`, temporary-directory allocation, helper sourcing, and `act`/`podman` probes. A missing workflow prints an explicit SKIP, states that no checks ran, and exits with documented code 3. A present workflow with an absent or unreadable helper reports a setup diagnostic on stderr and exits 2. For a readable helper and committed workflow, the existing runner continues through the same tool validation and job execution path.

The two regression cases create committed fixture repositories and assert the skip return code/message and the missing-helper error. Their fixture setup supplies child environments explicitly. Static checks performed by this seat: `bash -n scripts/local-ci.sh` and `git diff --check origin/main...3734816f969c1a4bcf82e2396872087ec8b36243` passed. Execution evidence supplied by the parent: targeted regression tests 2 passed; `make check-fast` 962 passed; `make lint` 182 passed. This seat did not execute those tests under its read-only constraint.

Verdict: approve

## Raw final report: consistency

# Consistency review — PR #1368

Anchor: `3734816f969c1a4bcf82e2396872087ec8b36243`; base: `origin/main`.
Perspective: consistency only. Reviewed the three supplied changed files, shell conventions, the neighboring subprocess test and child environment helper, and ticket format rules. HEAD and the changed-file roster match the supplied anchor; `git diff --check` passes. No tests run by this seat.

## Finding

- **Minor; confidence high — verifiable:** Ticket context identifies the wrong repository and decision. At `3734816f969c1a4bcf82e2396872087ec8b36243:tickets/1088-local-ci-skips-cleanly-when-the-reposito.erg:13`, “this project is one; see decision 0321” claims this repository intentionally has no CI. `git -C /tmp/idh-t1088-local-ci-skip ls-tree --name-only 3734816f969c1a4bcf82e2396872087ec8b36243 .github/workflows/CI.yml` returns `.github/workflows/CI.yml`, and this repository's 0321 is `tickets/closed/0321-gaze-fork-liveness-contract-bounded-wind.erg`, about gaze liveness. Name the consuming climate-finance repository explicitly and qualify its decision reference, so the shared-runner ticket remains accurate in the harness repository.

The script retains documented exit 3 for missing workflow and uses the existing exit 2/stderr convention for setup errors. Explicit SKIP/stdout is appropriate for the requested outcome. The subprocess tests use the established `child_env()` pattern and the positive workflow fixture distinguishes the two requested branches. No further consistency findings.

Verdict: comment

## Raw final report: scope

# Scope review — PR #1368

Anchor verified with the review-pr anchor helper: HEAD `4126c263034384a46e162599829afeb977cfab8e`, base `refs/remotes/origin/main`. The helper succeeded under elevated network access after sandboxed forge access failed.

Changed roster: `scripts/local-ci.sh`, `tests/test_local_ci_no_workflow.py`, and `tickets/1088-local-ci-skips-cleanly-when-the-reposito.erg`.

No scope findings. Confidence: high.

The script diff moves the existing no-workflow exit ahead of helper loading, prints the requested explicit skip/no-checks diagnostic with exit 3, and adds the requested missing-helper diagnostic with setup exit 2. It leaves the remaining CI validation and execution code unchanged. The new test file exercises exactly these two preflight paths in temporary repositories. The ticket records the same scope and now correctly attributes the no-CI decision to climate-finance-het. No workflow, runner assets, dependency changes, or unrelated refactoring are added.

This seat assesses scope only; it does not certify test execution or the merge gate.

Verdict: approve

## Raw final report: red_team

# Red Team review — PR #1368

Anchor: `4126c263034384a46e162599829afeb977cfab8e`; GitHub `gh pr view` confirmed this open PR head against base `main`.

Verdict: APPROVE. No blocking findings.

Severity: none.

Evidence:
- The no-workflow path checks the committed `HEAD:.github/workflows/CI.yml` before helper readability, temporary directory creation, helper sourcing, and container tool checks. It explicitly says `SKIP`, that no checks ran, and exits 3, preserving the documented nonzero no-workflow contract.
- A committed workflow plus absent/unreadable helper exits 2 with a setup diagnostic. This cannot be reported as a passing run.
- Root resolution and the quoted `git -C "$root"` invocation handle invocation from subdirectories and repository paths containing spaces. The workflow path is fixed and interpreted relative to the committed tree, so untracked or modified workflow files cannot produce an apparent CI pass.
- The existing runner flow, strict-skip behavior for individual jobs, and exit-0 success path are unchanged after preflight.
- The new subprocess tests exercise both states with actual temporary git commits and assert the distinguishing exit codes and messages.

Limitations: read-only static review; no tests executed by this seat. Git object/database failure can still share the absent-workflow branch because `cat-file` failure is treated as missing; that classification predates this change, returns nonzero, and does not falsely declare a pass.

## Raw final report: doc_propagation

# Documentation propagation review — PR #1368

Verdict: APPROVE. No blocking documentation propagation finding.

Anchor: local HEAD and forge PR head both `4126c263034384a46e162599829afeb977cfab8e`; forge readback reports OPEN, base `main`, https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1368. Reviewed the three-file diff against `origin/main`.

Evidence:
- `scripts/local-ci.sh:26-29` continues to document exit 3 for a repository with no workflow at HEAD. The moved preflight and explicit SKIP/no-checks-run message at lines 36-38 implement that existing contract; ticket 1088 Actions and Exit criteria use the same code and terminology.
- `tickets/closed/1041-local-ci-runner-equivalent-to-the-forge-ci.erg:43` already records no-workflow exit 3 as “not a pass”; this PR preserves that historical contract and needs no retroactive ticket edit.
- Climate-finance's local `tickets/closed/0321-main-is-red-8-ruff-findings-and-a-tier-3.erg`, Decision section, records the author's explicit no-workflow decision. Ticket 1088 accurately cites it and the change adds no CI assets to that project.
- The committed test assertions distinguish exit 3 with a SKIP and no-checks-run output from exit 2 with missing-helper setup error. No changed public command name, configured-workflow execution behavior, or gate policy needs propagation into README or the historical merge-gate specification.

Low-priority wording observation: `scripts/local-ci.sh:14` says “The first output line names the UTC time, the actor and the host.” The early no-workflow SKIP now precedes that trace line and contains no trace fields. Qualifying this comment as applying to configured workflow runs would make it literally accurate. This is a header-comment precision issue, not a behavioral blocker or a false pass.

Review was read-only apart from this report. No tests run by this seat; no forge review posted.

## Raw final report: red_team_cross_family

# Cross-family red-team review — PR #1368

Anchor: `03963c9f135c06efefb7e562f2177d96589de1d9`. Runtime: Claude Code; requested model `claude-sonnet-5-5`, effort medium. Telemetry modelUsage canonicalModel: `claude-sonnet-5-5`; provider `firstParty`; cost USD 0.29034.

**Verdict: APPROVE.** Highest severity is Low, and nothing blocks the merge.

I reviewed the pasted diff only. I did not run the tests, the runner, `act` or `podman`. Line numbers below are derived from the hunk offsets, so treat them as approximate.

**Exit criteria**
- **No workflow gives 3 before helpers and tools.** `scripts/local-ci.sh:37-40` runs `git -C "$root" cat-file -e "HEAD:$workflow"` and exits 3 with `SKIP` on stdout. It comes before `here=`, `mktemp`, `. common.sh` and `start_service`/`ensure_image`. The old late check is removed, so there is no second path. The change also stops leaking the temp dir on skip.
- **Workflow present but helper missing gives 2.** `scripts/local-ci.sh:43-46` tests `[ ! -r "$here/common.sh" ]` and exits 2 with the message on stderr. This runs before the `source`, so `set -e` can't turn it into a bare failure. `$here` is derived from the target repo's `git rev-parse --show-toplevel`, not from the runner's own location, so the test's use of a temp repo is valid.
- **Tests cover both paths.** `test_no_workflow_is_a_successful_skip_before_local_helpers` asserts 3 and the three message fragments, which match the emitted text. `test_workflow_without_local_helpers_is_a_setup_error` asserts 2 and the stderr text.

**Findings (all non-blocking)**
1. **Low: a skip can mask a setup failure.** `scripts/local-ci.sh:37` sends stderr to `/dev/null` and treats any failure of `cat-file -e` as "no workflow". An unborn HEAD (repo with no commits) or a damaged object store would therefore report a clean skip with 3, though neither is an intentional no-CI repo. Fix: run `git rev-parse --verify -q HEAD` first and exit 2 if it fails. Then only a real absence of the file maps to 3.
2. **Low: the "before tools" claim is only indirectly tested.** Nothing asserts that `act` and `podman` are never probed. The tests would pass if a tool probe sat before line 37, as long as it didn't fail. A stricter test would run with a PATH that has no `act` or `podman` and check that the result is still 3. It could also check that the workflow-plus-missing-helper case never prints `SKIP`.
3. **Low: the test name contradicts the contract.** `test_no_workflow_is_a_successful_skip…` describes a skip as successful, but 3 is non-zero and the script's own message says "not a pass". Rename it, for example `…_is_a_labelled_skip…`. The ticket title "skips cleanly" has the same problem.
4. **Info: the skip message moved from stderr to stdout.** The old message was on stderr. A caller or hook that treats a non-empty stderr or exit 3 specially could notice. The exit code is unchanged, but I haven't checked callers of exit 3 and they should be grepped before merge.
5. **Info: the ticket text names a private repo.** The public ticket names `climate-finance-het` and "decision 0321". That is probably harmless, but check it is meant to be public.

**Preservation of configured CI behavior.** Only two things change for repos that have a workflow and helpers. The no-workflow check now runs before the trace header and the "uncommitted changes" warning, and a skip prints no header. Both are consistent with the updated header comment. The rest of the flow after `common.sh` is untouched in the diff.

**Limitations**
- I could not see lines 1–31 of `local-ci.sh`, `ci-local/common.sh` or `child_env`. I can't rule out an earlier tool probe, other uses of exit 2 in the script, or git config such as commit signing leaking into the test repos.
- No test covers the happy path (workflow plus helpers plus `act`). "Existing CI repositories retain all current behavior" rests on the diff reading, not on a test.
- The ticket's `make check-fast` and `make lint` boxes are unchecked, and I verified neither.

Orchestrator dispositions: no changes requested by this seat. The unborn/corrupt-HEAD classification predates this change and remains nonzero; extra PATH probe assertions and naming are optional coverage/wording suggestions; stdout is the deliberate SKIP interface; the existing public ticket context is scoped to the user-authorized defect. No blocking issues.
