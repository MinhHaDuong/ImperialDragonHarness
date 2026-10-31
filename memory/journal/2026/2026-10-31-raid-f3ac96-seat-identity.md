# Raid f3ac96: seat identity from the launcher header; local seat family from the served model (2026-10-31)

Context: interactive session on padme (claude-opus-5-5), following the
cross-family gate drop (journal entry 2026-10-31-cross-family-gate-dropped).
The author ruled that model identity and access are distinct, and that "Local"
is access, not a family.

Events:
- PR 2093 (explore-local-seat-family): gaze_seat.py now stamps a local seat
  with the grid `family` of the model id the server lists, or `unknown` when
  the id is in no grid row. `local_family` was removed from routes.json and
  `local` from review_evidence FAMILIES, which reverts PR 2066. Gaze REVIEWED
  (one Sonnet seat, two consider notes not adopted), verify-gate APPROVED in
  round 1, merged at 7de95c67.
- Raid f3ac96, ticket 1388, run as an explicit `/raid 1388`. The single-ticket
  Imagine and Plan phases were done inline by the orchestrator rather than by
  agents. One Sonnet coder ran hunt and opened PR 2094, which changes
  `seat_clock.identities()` to trust a `door=headless` launcher header even
  when the plan's reason column names no door. Corrections were appended to
  the PR 2073 and PR 2085 attribution records. Gaze REVIEWED with a script
  check only. verify-gate APPROVED in round 1 with one consider note: a
  subagent seat that writes `door=headless` itself would now be believed.
  Merged at 86f66bec.
- Capture failure: `attribution_record.py --capture-unit pr:2094` printed
  `not derivable: reviewers` and wrote no record. The gaze answer had no model
  seat, only a script check of family none.
- The PR 2093 record carries `runtime=claude` for its seat. That runtime came
  from a first launch on a wrong door name, which gaze reported.

Outcome: both PRs merged. The after-merge full-suite run on main was started
by the sync and was not awaited.
