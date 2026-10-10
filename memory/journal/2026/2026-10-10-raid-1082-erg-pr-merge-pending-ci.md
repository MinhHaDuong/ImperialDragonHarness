# Raid 1082: erg-pr-merge arms auto-merge on pending CI (2026-10-10)

Continues [merge script CI refusal and ticket 1082](2026-10-10-merge-script-ci-refusal-and-ticket-1082.md). PR #1352; ticket 1082 closed by it.

## Observed
- Launch line: `sonnet | Anthropic | coder profile | ordinary build | bounded shell and tests change`. The raid skipped its Imagine, Plan and feasibility phases for the single ticket and checked the premise directly (the `PENDING` refusal was still at `skills/merge/erg-pr-merge:148` on `origin/main`).
- The coder agent opened PR #1352 (8 files) and reported `scripts/local-ci.sh` 10 passed, 1548 tests passed. It worked inside the orchestrator's own worktree, not one of its own, and pushed the local branch `worktree-t1082-1235863` as `t1082-pending-ci-auto-merge`. `erg-pr-merge` then refused ("must run from PR branch 't1082-pending-ci-auto-merge'") until the local branch was renamed.
- `/gaze` round 1 returned REROLL on tip `fbd9b637` with three verified findings: `skills/roar/SKILL.md:32` used an `IDH_ROOT` that was not set at that point; the unavailable-auto-merge message in `erg-pr-merge` told the caller to merge once `erg-pr-status` exits 0, which means already merged; stale "watch-then-merge" wording in one script comment and three test comments. Seat B and the five-perspective panel found no blocking correctness defect. The adherence seat did not run (the session isolation guard refused its git access to the review worktree). All seats were Sonnet. The orchestrator fixed the three items (`4e2589ea`) and logged `note verify-reroll` on the ticket.
- A cross-family seat for the high-risk band was attempted through `codex exec -s read-only -m gpt-6-luna` and failed at once with "You've hit your usage limit … try again at Oct 14th, 2026 8:11 AM"; no review was produced. The Pi door was not used (only Hugging Face models configured on padme; spend and read-only behaviour unverified).
- `/gaze` round 2 returned APPROVED on `4e2589ea` with `battery: NOT-RUN — cause: guard` and `panel integrity: DEGRADED`; the 17-line fix delta was checked by the gaze agent itself. CI on that tip: 10 of 10 passed. `erg-pr-merge` merged #1352 at 2026-10-10T17:31:13Z.
- First run against the real forge: `skills/merge/erg-pr-status 1352` printed `PR #1352: merged` and exited 0.
- A repo-wide search for skills using `IDH_ROOT` without defining it returned self-contradictory output (it listed `skills/roar/SKILL.md` as lacking an assignment that had just been added) and was discarded as inconclusive.

## Disclosed gaps
- No other-family reviewer saw #1352; the merge-gate change carried same-family review only.
- The failing-check filter (`FAILURE`, `TIMED_OUT` only; `CANCELLED` and `STARTUP_FAILURE` are skipped) predates the ticket and was left unchanged.
- No run on doudou; the new tests stub the forge. The ruleset's required-check set was not confirmed against early arming of auto-merge.
- No review-attribution record for the Sonnet gaze seats or the Codex attempt: the seat model ids were not available to the orchestrator verbatim.
