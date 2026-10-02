# Memory v8 delivery merge under parallel housekeeping (PR #1102)

PR #1102 delivered the memory v8 convention and inventory (0911, 0917) and
retired the remaining native/shared-store DREAM helpers (`commit.py`,
`read-index.py`, `provenance.py`) with their consumer tests. Two Copilot
review threads flagged that `memory/MEMORY.md` claimed "no cross-project
pooling" while `scripts/on-start.sh` still injects the index into every
Claude Code session, and that the closure batch was not propagated to
STATE, ROADMAP and the 0999 tracker.

The review-bot fixes never reached the PR: its pushes were rejected, so its
repair commits existed only in its own sandbox. A session with push rights
redid both fixes in `bce2b897` (index and hook comment now describe the
injection as a legacy channel pending retirement; coordination files
propagated the closure), with the census hook budget still passing at
497/500 chars.

At the merge gate the mandatory rebase onto main showed that parallel
housekeeping (#1106, #1107) and the integration closure (#1099 WONTDO 1002,
#1101 retiring provenance, #1104 closing 0999) had already landed much of
the same coordination propagation. Conflict resolutions took main's
authoritative closure records for 0934 and 0999, kept the branch's
0911/0917 delivery facts, and reduced the review-fix commit to its
still-relevant parts. `tests/test_dream.py`, deleted by the branch and
modified by #1101, was deleted with the helpers it tested.

The PR body originally used GitHub-issue syntax ("Closes #0911") that
`erg-pr-merge` cannot read; machine-readable `**Ticket:**` lines were added
for the five closed tickets (0911, 0917, 0991, 0934, 1002), all already
closed and archived, so the merge script treated each as a clean no-op.
Post-rebase verification: `erg check` 515 tickets, `git diff --check`, and
the full suite 1,212 passed and 2 skipped. All ten GitHub checks passed
before the merge; PR #1102 merged as `c596f3bb` and local main
fast-forwarded. Pilot 0920 is unblocked; 0913 retains the rollout.
