# Gate record lost by a shared-ref rewind (ticket 1366, PR 2033)

Context: the after-merge record for main tip 0645f247 (2026-10-29) reached
the local refs/notes/gate but never origin's; no "notes push rejected"
warning was logged. The ticket named two candidates: forge read-after-write
lag, or an unreported push failure.

Events:
- Raid 85542d reproduced a third mechanism with a bare remote: append to
  refs/notes/gate, a forced `fetch +refs/notes/gate:refs/notes/gate` (what
  `fetch_notes` does, from any process sharing the repository's refs), then
  `git push origin refs/notes/gate:refs/notes/gate` exits 0, sends nothing,
  and the remote keeps the old tip. A push by commit id lands.
- Forge lag alone did not fit the incident: the next writer's non-forced push
  at 00:38:21 succeeded with no rejection, so origin did not hold the record.
- PR 2033 builds the append on a per-process ref, pushes by commit id, reads
  the remote back (`ls-remote`, ancestry through a private probe ref), warns
  "push reported success but the remote lacks the record" or "cannot verify"
  distinctly, raises only on proved absence, and keeps an unpublished record
  on refs/notes/gate on every failure exit. main_sweep's "runner crashed"
  label became neutral.
- Gaze took five rounds with a codex (openai) red-team seat: FINDINGS on
  8bb46119, a7fc8b4e and ee387e0e (all error-path accuracy), REVIEWED on
  9a7c8a35. One round-3 record carried `seats: self-only` although its text
  named a codex seat that ran, so it counted as no record and gaze ran again.
- verify-gate round 1 APPROVED on 92417559; landed with raid_land.py as
  1493043e.

Outcome: the incident itself was not replayed; the mechanism was. From
1493043e on, a recurrence logs one of the two warnings above.

References: tickets/closed/1366-after-merge-record-lost-notes-append-rew.erg,
PR 2033, review rv-20261030-pr-2033-5c01.
