# PR 2442: verify-gate asked for an author ruling the author had already given in conversation

Date: 2026-11-10. Project: harness. PR #2442 (ticket 1443).

## Context

The author asked whether memory v8 matched its design note, then agreed to an
as-built blueprint and said "Go ahead and close the ticket" for ticket 1443,
whose questions were folded into `design/memory-v8/README.md` § Open design
questions. Two of the ticket's three exit criteria (guarantees arbitrated with
the author; locations identified) were not met by design: the ticket was
closed as a parking decision, not as completed work. The author then said
"merge".

## Observations

- `merge-gate.py tier` read the diff as full tier (design docs, memory
  topics, ticket move), so gaze and verify-gate were required.
- Gaze (one Sonnet seat, a script check and self) answered REVIEWED at
  `e68654e` with no blocking finding.
- Verify-gate (session `5c10cd50-7ea1-4d1e-8203-b49e3607bfec`) ruled
  NEEDS-AUTHOR, not REROLL: criteria 2 and 3 MISSING, and the only record of
  the author's decision was agent-written. The ticket log line carried git
  name `reviewer`, and PR comments posted under the author's forge login were
  agent-made, so the gate could not tell an author act from an agent one.
- The session posted a PR comment quoting the author's two conversation
  turns, then merged with `--match-head-commit`; read-back `MERGED e68654e`.

## Outcome

Merged as `2337c3a`. The NEEDS-AUTHOR round cost about two minutes; no
reroll. Cause of the visibility gap (agent identity shared with the author's
login and the generic git name) not further isolated.

## Evidence

- PR #2442 comments (gate verdict pointer, author-ruling quote).
- Review `rv-20261110-pr-2442-7864` on `refs/notes/review`.
- `tickets/closed/1443-repenser-la-m-moire-statut-de-premier-ra.erg`.
