# Consistency review — PR #1377

Anchor: `17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92` against `origin/main`. The pre- and post-review anchor checks agree on the head and the five changed paths.

Verdict: **comment** (high confidence).

The principal native/red-team finding is fixed: self-exclusion now requires both the current branch and local `origin` repository identity to match `headRefName` and `headRepository.nameWithOwner`. The prior single-foreign-PR/same-branch false exclusion is covered directly, as is a successful `gh pr view` result for a foreign PR. Failed or empty PR lookup falls back to repository/branch matching; missing or ambiguous identity exits 2 without renumber advice. Explicit `SELF_PR_NUMBER` and the no-ticket fast path remain intact. All four forge calls have `harness-extension-point` markers on the call or immediately preceding line, matching `scripts/check-agnostic.sh`'s rule.

The old red-team wording finding is also resolved: the warning now says lookup was “unavailable or no open PR.” Its ticket-closure concern is addressed: the archived ticket marks all four exit criteria complete and records real-PR #1374 evidence plus passing full-suite and lint runs. Ticket 1091's wave annotations do not alter its exit criteria and stay within that ticket's census scope. The remaining old low-severity observation about cosmetic indentation is not actionable.

- `verifiable:` (confidence: high) When a base-tip collision is found and self repository identity then cannot be established, the script prints the base collision at lines 89–91 but exits 2 at lines 115–117 before reaching the collision exit-1 block at lines 156–162. This gives a known collision the unresolved-identity exit status and omits the renumber guidance. Consider preserving/reporting the collision exit status while still surfacing the identity failure, or documenting the precedence. Evidence: `17a0c63ebc82a72ece4b4514a98bf5b2dcd18c92:scripts/check-cross-pr-ticket-collision.sh:115`.

Validation: `bash tests/test_check_cross_pr_ticket_collision.sh` passes all 17 controls, including the fork identity regressions. `scripts/check-agnostic.sh scripts` passes. Earlier artifacts `native-review.md` and `red-team.md` were read and reviewed against the current changes; their central false-exclusion finding and the missing single-fork control are both addressed.
