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

- `tickets/erg-github` (this repo) -- **FIXED 2026-09-16**, ticket 0255,
  PR #339. The fix is not the obvious one: adding `(closed/)?` to the grep
  while leaving the BRE `sed` case-sensitive created a *worse* defect, because
  `grep -i` folds case for every literal and the sed folds none. A mis-cased
  `TICKETS/` or `Closed/` then cleared the filter, failed to substitute, and
  either leaked the whole body line as an id or -- after a shape guard was
  added -- emptied `$ids` into the escape hatch, passing the required CI gate
  for a still-OPEN ticket. The landed fix folds case ONCE up front (`tr`) and
  drops `grep -i`, so filter and substitution cannot disagree about any
  literal, present or future.
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

**How to apply:** the harness copies are still live and are the ones that run
at most merges, so the workaround stands there -- do not pre-close a ticket
before running the merge; let the merge script close it. When 0929 is worked,
take git-erg's landed shape (fold case once, drop `-i`) rather than
re-deriving it: the two intermediate attempts are both recorded above as worse
than the original defect, and the second was a *fail-open* bypass of a required
gate, which is the failure mode to avoid re-inventing.

**Test-shape lesson from the same fix.** The round-1 test asserted exit 0 and
no leak, and passed against the fail-open bypass, because an escape-hatch PASS
and a real PASS are both exit 0. A test here must pin the *branch taken* --
assert the specific `ticket NNNN is closed in this PR` message -- not the exit
code.

Related: [[bare-gh-pr-merge-drops-close-claim]], [[verify-delivery-gate-runs-check]].
