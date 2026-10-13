# Doc propagation — PR #1377

Perspective: doc propagation. Anchor passed before and after review at `17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92`, base `origin/main`. Changed files: `scripts/check-cross-pr-ticket-collision.sh`, `tests/test_check_cross_pr_ticket_collision.sh`, open ticket 1091, open ticket 1092 moved to `tickets/closed/1092-check-cross-pr-ticket-collision-reports.erg`.

The script’s header now reflects its four marked forge calls: `gh pr list`, `gh pr view`, `gh repo view`, and `gh api` for sibling files (lines 17–19, 98, 107, 115, 137). `SELF_PR_NUMBER` is documented as an override with inference as the default (lines 21–27). The documented no-ticket fast path still exits before any forge call (lines 63–65). Exit 2 covers inability to list PRs or establish self identity; ambiguity and missing source identity emit that error without renumber advice (lines 98–100, 115–122). The new controls exercise override bypass, no-ticket fast path, list failure, source identity failure, ambiguity, successful/missed/failed lookup, a branch with no open PR, and foreign same-name branches (test lines 313–394).

The PR body matches the implementation and evidence: it describes self inference, visible lookup recovery, ambiguity handling, explicit override and fast path, and cites real PR #1374 tests with `SELF_PR_NUMBER` unset and with forced lookup failure. The full-suite log records 1603 passed and 4 skipped; the fast and lint logs record 964 and 182 passed. The body does not claim that ticket 1091’s resident-census behavior was tested; the 1091 diff is shared-wave annotation only. Its statement that the plan annotations came from the supplied wave base is consistent with the prior review head. No README or other downstream usage documentation describes this script’s former two-call count.

The earlier native and red-team fork-identity findings are fixed: the list includes `headRepository`, and inferred self exclusion matches both `headRefName` and the resolved local source repository. A single foreign fork with the same branch name remains scanned, with a regression control. The earlier closure-evidence finding is also addressed: all four 1092 criteria are checked, and the closed ticket contains evidence for the real #1374 normal and forced-lookup-failure runs, the hermetic positive control, and the full check. No unsupported primary-checkout claim was found.

Finding:

- `consider:` [Low, confidence high] The test file’s opening case inventory still stops at cases (a)–(g), while the file now adds case (h) and several unlettered lookup, source-repository, and override controls (`tests/test_check_cross_pr_ticket_collision.sh:18-29`, `313-394`). Updating that inventory would make the test’s overview reflect its expanded coverage.

Verdict: comment.
