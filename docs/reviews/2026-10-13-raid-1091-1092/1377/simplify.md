# Simplify review — PR #1377

Reviewed SHA: `5a0600a24369fb3780f72505a99d367fd29c1f73` against `origin/main`.

Verdict: **CLEAN**.

The previous MINOR candidate is resolved: `gh pr view`, whose result was discarded, is removed. Self inference now uses the actual open-PR list and requires both the current branch and proven local origin repository to match. The lookup-only stub state and duplicate lookup-miss/failure control are also removed. The remaining cases preserve meaningful coverage: own PR exclusion, true sibling collision, branch with no open PR, foreign same-name fork, same-name local and foreign branches, missing/ambiguous source identity, explicit override, and the no-ticket fast path. I found no further simplification that reduces complexity without weakening these behaviors or the ticket's exit criteria.

The earlier exit-2 precedence observation is addressed by documenting that inspection failure takes precedence after a base-tip collision and suppresses renumber advice until self identity is known. This is explicit fail-closed policy, with no remaining simplify finding.

Evidence checked without rerunning tests: the final shell log ends with PASS; the full-suite log reports 1603 passed and 4 skipped; the real-PR log reports no collision for PR #1374. The final anchor remained `5a0600a24369fb3780f72505a99d367fd29c1f73` after review.
