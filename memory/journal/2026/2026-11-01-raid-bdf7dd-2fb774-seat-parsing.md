# Raids 2fb774 and bdf7dd: seat header parsing (2026-10-31 to 2026-11-01)

Context: the author asked for tickets 1399 and 1400, then an inspection of the review-seat header
parser ("the kind of thing that drifts fast"), then ticket 1389 and two small items.

Observed:
- The read-only parser inspection reproduced on main two mis-acceptances: a second contradictory
  reach line was ignored, and a full answer quoted in Aider reasoning upgraded a real `read=no` to
  `read=yes shell=yes tests=ran`. It counted three header-parsing sites with different
  normalisation. PR #2115 (1400) refused contradictory reach lines and introduced one shared
  extractor; PR #2118 (1389) took the Aider answer from the last framed marker.
- Ticket 1389 existed only on another session's unmerged local branch
  (`tickets/arena-aider-parser-20261031`, e56955a7). It was copied onto a fresh branch without
  that branch's edit to the closed tracker 1382; the original branch and worktree were left untouched.
- PR #2110 (1399): the cross-family red-team seat found two forgery paths (stale launch line,
  `-` unit wildcard) that the nested gaze had downgraded without probes; a fix round closed both.
- PR #2119 (no ticket): two gaze runs launched inside the coder subagent were self-only, wrote no
  answer on notes and left a `review-2119` worktree. A gaze run from the orchestrator session found
  a blocking crash (keep_raw caught only OSError; `archive_root()` raises RuntimeError since t1402).
- PR #2118: the first cross-family seat (codex, gpt-6-luna) returned NOT-RUN for lack of a read
  tool; the re-run with gpt-6.1-sol ran 1,440 adversarial cases. Merging main surfaced a fast-tier
  marker violation (subprocess test without `integration`), fixed in its own commit.
- PR #2115: GitHub kept the PR head at the commit before the pushed ticket close for over five
  minutes while the branch ref held the new tip; the first merge call was refused. Closing and
  reopening the PR resynced it, and the merge then went through pinned to the ruled tip.

Outcome: 1389, 1399 and 1400 closed; PRs #2110, #2115, #2118, #2119 merged; each gate APPROVED in
round 1.
