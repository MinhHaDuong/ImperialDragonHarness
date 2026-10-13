# PR1377 Red team review (code-reviewer seat, claude-sonnet-5-5, medium; non-OpenAI family)
Reviewed SHA: c21e841bdb33c4f9cec793b6d68dedca1f8ae6a5 (base refs/remotes/origin/main). Anchor script run before and after: HEAD matched both times.
Scope read: scripts/check-cross-pr-ticket-collision.sh, tests/test_check_cross_pr_ticket_collision.sh, tickets 1091 (wave annotations) and closed/1092.
Ran: `bash tests/test_check_cross_pr_ticket_collision.sh` -> all 14 PASS (stubbed gh only; no real-forge run). Plus /tmp experiments below.

## Findings
1. [MEDIUM, confidence high] Branch-name-only fallback excludes a foreign-fork PR -> real collision missed (fail-open). script:116-125 (`select(.headRefName == $branch)`; list requested with only number,headRefName at line ~98).
   Evidence (/tmp experiment, stub gh): local branch `fix` adds tickets/0300-own.erg; `pr view` fails/misses; open list = [{55,"fix"}] (a fork PR from another repo's `fix`) whose files add tickets/0300-theirs.erg. Result: "no open PR claims the same ticket ID(s) — OK", rc=0. Pre-PR behaviour would have named #55 (rc=1). Native finding validated. Needs headRepositoryOwner/isCrossRepository in the list and matching on it. Mitigated in CI (workflow sets SELF_PR_NUMBER, CI.yml:34), so exposure is local/worktree runs, the very case this PR targets; common branch names (`main`, `fix`, `patch-1`) make fork collisions realistic.
2. [MEDIUM, confidence high] Test suite has no fork/same-headRefName control; the "ambiguous" test (exactly two same-named PRs) passes but the single-foreign-match case, the dangerous one, is untested. tests:~345-352. Single same-named foreign PR is silently treated as self.
3. [LOW] Detached HEAD with unset SELF_PR_NUMBER exits 2 even when `gh pr view` could not help and no collision exists (experiment rc=2). Fail-closed and documented, acceptable; but the exit-2 message emitted after base-tip COLLISION lines already counted, so a true base-tip collision is reported as exit 2 (uncertainty) not 1. consider: move base-tip verdict before/independent of self resolution.
4. [LOW] Misleading WARNING "self PR lookup failed" printed for the normal case "branch has no PR" (gh pr view exits 1 on no PR). consider: reword.
5. [PROCESS, MEDIUM] tickets/closed/1092: `Closed: implemented` while all three exit criteria remain `[ ]`, including "verified against a real open PR"; the diff shows only stub tests, no real-PR validation. Ticket is closed inside the PR itself, before merge. verifiable: `git -C $T show c21e841b:tickets/closed/1092-check-cross-pr-ticket-collision-reports.erg | grep -c '^- \[ \]'` -> 3.
6. nofollow: tests/…collision.sh apifail case (~line 199-204) has misindented duplicated env forwarding lines (cosmetic, harmless).
7. nofollow: explicit override verified: SELF_PR set -> `gh pr view` never called (test + code at the `-z "$SELF_PR"` guard). True collision preservation verified by tests (named #77, rc=1). 1091 annotations are ticket-note only; no code touched; consistent with its stated scope.

## Not established
No run against a real GitHub forge; malformed (non-JSON) `pr list` output reaches jq under set -e and would exit non-0/5 rather than the documented 2 (untested; consider:).

## Verdict: request-changes (finding 1, with finding 2 test; finding 5 to be resolved or acknowledged by author)
