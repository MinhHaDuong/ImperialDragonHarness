# PR1377 Red team re-review (code-reviewer seat, claude-sonnet-5-5, medium; non-OpenAI family)
Reviewed SHA: 5a0600a24369fb3780f72505a99d367fd29c1f73 (base refs/remotes/origin/main). Anchor helper run before and after: HEAD identical. Prior report kept as red-team-initial.md.
Verified independently (not from producer claims): current diff read; targeted `bash tests/test_check_cross_pr_ticket_collision.sh` -> 16 PASS + summary line, no FAIL; read-only `gh pr list --json headRepository` against the real forge shows `headRepository.nameWithOwner` exists and `gh repo view <origin url>` returns MinhHaDuong/ImperialDragonHarness (so the match key is real, not a stub artefact); own /tmp clone checked out at PR #1374's head branch, SELF_PR_NUMBER unset -> exit 0, "no open PR claims the same ticket ID(s)" (IDs 1089/1090 added by the PR itself, so exclusion of #1374 is demonstrated); same clone, detached HEAD -> exit 2 with "set SELF_PR_NUMBER (no renumber recommendation)". Full suite not re-run (out of scope).

## Disposition of prior findings
1. Foreign-fork same-branch false exclusion: FIXED. Exclusion now requires headRefName AND headRepository.nameWithOwner == origin's resolved repo (script:~111-122); no name-only path remains. Hermetic fork control exists in the suite. Resolved.
2. Missing fork test: FIXED (fork, no-own-PR, source-identity failure, ambiguity, override controls present).
3. Detached HEAD / base-collision exit precedence: FIXED by documentation; header states inspection exit 2 overrides earlier base collision reporting. Behaviour confirmed (rc=2 detached). Acceptable.
4. Misleading "lookup failed" warning: FIXED (gh pr view removed; 3 marked forge calls remain).
5. Ticket 1092: all 4 criteria now `[x]` with evidence (real PR #1374 validation, hermetic controls, make results). Resolved; the 1603/4-skip full-suite claim is the producer's log, not re-run by me.

## New findings
- [LOW, confidence medium] consider: `gh pr list` default limit is 30 (pre-existing, unchanged); with >30 open PRs, siblings or self may be missing — missing self degrades safely to scanning all, missing siblings fails open. Not introduced here.
- [LOW, confidence medium] consider: a clone whose `origin` is a fork while the PR's head repo is that fork works; a local remote named other than `origin` (e.g. only `fork`) exits 2 with explicit advice — fail-closed, acceptable.
- nofollow: header comment line about forge calls is overlong (cosmetic). nofollow: explicit SELF_PR_NUMBER still bypasses all inference, including `gh repo view` (covered by test).
No blocker found; true-collision preservation (sibling named, exit 1) still passes.

## Verdict: approve (this seat; not a merge/gate decision)
Head 5a0600a24369fb3780f72505a99d367fd29c1f73. Artifact: .panel/1377/red-team.md
