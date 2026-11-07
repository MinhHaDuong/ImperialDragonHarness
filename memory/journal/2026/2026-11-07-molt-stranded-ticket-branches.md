# Molt found ticket filings stranded on idle branches — 2026-11-07

Context: on doudou, a yawn and molt sweep of the harness (PR #2227, a
STATE.md bookkeeping fix, merged as 7680ddb0). Yawn listed five unmerged
remote branches idle 6–9 days as cleanup candidates.

Observed: two of the five held filings that had never reached main.
`explore-dsh-superagent` (2026-11-01) held conception/2026-11-01-dsh-superagent-ideas.md
and tickets 1440–1442. `gaze-schema-followup` (2026-10-30) held ticket 1377.
None of these IDs had been reused on main. The other three were superseded:
`hoard-2026-10-29` by the 2026-11-01 smelt (#2197), `t1375-scrub-gaze-close`
by 1375's close (PR #2060 plus the author's 2026-10-30 ruling), and
`tickets/arena-aider-parser-20261031`, whose harness tickets 1382 and 1389
were already closed on main. The session first called that branch
cross-project on the strength of its name; its paths were harness tickets.

Outcome: the five files were cherry-picked unchanged into PR #2229. The
session had estimated it would land as bookkeeping with no review. The
`conception/` note made it full tier (bookkeeping paths in merge-gate.py:
tickets, STATE.md, memory/). Gaze rv-20261107-pr-2229-9b0c (FINDINGS, two
Anthropic seats) found that 1377 said raw seat output "is not retained",
which commit 2b5e2ce2 (keep_raw, landed the day after 1377 was filed)
contradicts. Log lines narrowed 1377 criterion 4 and gave 1440 a pointer to
PR #2214 and ticket 1180. Verify-gate APPROVED at f000e815; merged as
5c6f70f9. All five remote branches and the dead-locked explore worktree were
then removed. A padme session's message that #2229 was behind main arrived
after the merge; the gate record had been made on the candidate merged with
origin/main.
