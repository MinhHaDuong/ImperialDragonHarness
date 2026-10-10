# Ticket-line guard deleted from erg-pr-merge (ticket 1081, PR #1348)

- Context: `erg-pr-merge` died when a PR body carried no Ticket line. Ticket
  1081 was created as audit-only; the author corrected that the ticket should
  include the fix, and chose deletion of the guard per the guard doctrine.
- Measurement (derived, last 400 merged PRs, 2026-09-16..2026-10-10):
  `Ticket: none` 155, close claim 196, `Ticket-ref` 86, no ticket text 16.
- `check-close-claims.sh` joins from claims, so it cannot see a PR with no line.
- A narrower guard (die on a written-but-unrecognised Ticket line) was tried.
  Opus review round 1 found a prose bounce and silent drops of bulleted
  claims; round 2 found new silent drops (`Ticket :`, `Tickets:`, numbered
  bullets) introduced by the round-1 fix. The author then chose to delete
  that guard as well; the final revision was merged without a third review.
- Reviewers were launched with the alias `opus`; the runtime did not expose a
  verbatim model id, and the round-1 reviewer reported itself as the same
  family as the writer.
- `erg-pr-merge` refused once on a pending `pytest-guard` check (ticket 1082's
  case); a single later retry merged.
