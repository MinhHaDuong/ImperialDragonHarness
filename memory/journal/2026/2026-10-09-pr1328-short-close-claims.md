# PR 1328: short `Ticket: NNNN` close claims normalized

Date: 2026-10-09. Ticket 1079, PR #1328, merge commit f0f93a93.

## Events

- `erg-pr-merge` refused a body line `**Ticket:** 1075` ("no close-claim").
  The change resolves a 4-digit ID standing alone after `Ticket:` to the one
  matching `tickets/(closed/)NNNN-*.erg`, rewrites the forge body to the
  canonical path, reads it back, and proceeds. Zero or several matches keep
  the refusal.
- The PR was opened with `Ticket: none`; the author asked for a ticket, and
  1079 was filed after the code.
- While `/gaze` round 1 ran, the writer pushed an extra test commit
  (e4d5c022) after an author remark on a missing case. The gate refused to
  rule on a moved branch (ESCALATE). The /gaze report described the commit as
  not its own; it was authored under the author's git identity by the writer.
- Round 1's code reviewer found that the first lookahead `(?![0-9/])`
  rewrote `Ticket: 0312-foo` to `tickets/0312-fixture.erg-foo` and let
  `Ticket: 0312, 0313` close only 0312. Fixed with `(?=\s*$)`; positive
  control: the old lookahead turns the two new cases red.
- Round 2 gate: APPROVED on 95f3374e. Panel integrity DEGRADED (one model
  family). Merged through `erg-pr-merge`.

## References

- Review attribution: `memory/journal/2026/2026-10-09-review-attribution-pr1328.md`.
- PR comments 6083294693 (round 1), 6083428077 (round 2).
