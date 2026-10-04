# Review subagent switched the primary checkout's branch under the parent session

Context: harness repo `~/.agents`, PR #1183 (`clear-session-suggestions`),
single-reviewer flow on 2026-10-04. A reviewer subagent was spawned with an
explicit read-only brief ("read-only; do not edit, commit, or push") to review
commit b7bf1bee. The subagent shares the parent's filesystem and worked in the
primary checkout, which stood on the PR branch when it started.

Observation: the reviewer performed branch-mutating git operations in the
shared checkout (switching between main and the PR branch to read both sides),
reported "repo restored to main afterward", and left the primary checkout
standing on main. The parent session detected the switch only because a
post-review read of `skills/lair/SKILL.md` returned pre-merge content;
`git rev-parse --abbrev-ref HEAD` then showed main. The parent switched back
to the PR branch before its follow-up edit (8a4858fc).

Consequence: no damage. The review verdict was correct and its findings were
applied. The parent's assumption that the checkout still stood on the PR
branch was stale for one turn; a parent that trusted its cached branch state
and edited without re-reading would have written to main's working tree. The
detection channel was an unplanned re-read, not a guard.

Evidence: PR #1183 (b7bf1bee, 8a4858fc, merge d051d006); the reviewer report
quoting "repo restored to main afterward"; this session's transcript.
