---
name: ticket-regex-gap-two-copies
description: "The close-claim extraction regex drops tickets/closed/NNNN in BOTH tickets/erg-github:77 (git-erg, ticket 0255) and ~/.claude/skills/merge/erg-pr-merge:146 (harness, unticketed as of 2026-09-16)"
metadata: 
  node_type: memory
  type: project
  originSessionId: d344415f-fe91-458d-aa20-c1b5c8a66772
  modified: 2026-09-16T06:28:44.461Z
---

The `**Ticket:**` line in a PR body is parsed by a regex that matches
`tickets/NNNN` and not `tickets/closed/NNNN`. When a ticket is archived before
the merge, the close claim is silently skipped. Three copies of the same logic
carry the same gap:

- `tickets/erg-github:77` (this repo) --
  `grep -iE '^[*]{0,2}ticket:?[*]{0,2}:? *tickets/[0-9]{4}'`. Covered by
  **ticket 0255**, salvaged onto main 2026-09-16 in PR #337.
- `~/.claude/skills/merge/erg-pr-merge:146` (harness) --
  `grep -oiP '^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+'`. Now **harness
  ticket 0929**, filed 2026-09-16 in harness PR #915.
- `~/.claude/skills/roar/check-close-claims.sh:109` (harness) -- byte-identical
  to the line above, added to 0929 in harness PR #917.

**The third copy is the detector, and it shares the defect.** A body carrying
`tickets/closed/NNNN` fails extraction at line 109, then matches the
`Ticket: none | tickets/` classifier at line 115, so the PR is counted as an
*explicit no-close* and never reported. Verified with a positive control on
2026-09-16: the open-path body extracts `0276`, the closed-path body extracts
nothing and matches the classifier. Consequence: a `check-close-claims.sh`
report of "0 findings, N explicit no-close" does not establish that no claim was
dropped.

**Second defect, same parser: it is fence-blind.** The extraction is a
line-oriented `grep` with no notion of Markdown code fences, so a PR body that
*documents* the claim syntax carries live claims. Observed 2026-09-16: harness
PR #917's body illustrated the bug with a fenced example line in claim form, and
`erg-pr-merge` would have extracted it (the PR was merged with a plain
`gh pr merge`, so nothing fired). With an archived ID, step 1.5's
existence-at-tip guard aborts the merge; with an **open** ID it closes the
ticket spuriously. Recorded in harness 0929. Practical rule until fixed: never
put a line in the claim form in a PR body unless you mean it, including inside a
code fence.

**Why:** this is the failure mode behind git-erg PR #334 (2026-09-10, ticket
0276's fix on main while 0276 stayed open). It clears the severity floor --
state diverges silently and `erg check` passes either way. `/roar` step 7's
`check-close-claims.sh` joins from the merged-PR side and would be the one thing
that catches it -- except that it is the third copy, so it does not.

**How to apply:** fixing only the git-erg copy leaves the harness one live, and
the harness copy is the one that actually runs at most merges. When 0255 is
worked, file and fix the harness instance in the same pass, and treat this as a
class with a standing regression test rather than two point fixes. Until then,
do not pre-close a ticket before running the merge -- let the merge script close
it -- which is the workaround 0255's own body records.

Related: [[bare-gh-pr-merge-drops-close-claim]], [[verify-delivery-gate-runs-check]].
