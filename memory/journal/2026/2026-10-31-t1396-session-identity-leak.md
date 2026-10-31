# Ticket 1396: after-merge red from an inherited session identity (2026-10-31)

Context: after-merge red tickets 1386 and 1396 named
`test_gaze_close.py::test_self_seat_without_a_session_model_is_loud_not_invented`,
failing on some main tips and passing on others, including on a tickets-only
merge (PR 2091, 3f634b99).

Events:
- Reproduced: the test fails with `IDH_SESSION_MODEL` set and passes without.
  `raid_land.py --session-model` exports it; the after-merge runner started by
  the local-main sync inherits it.
- Fixed by PR 2097 (bdd2c597): an autouse fixture in `tests/conftest.py` deletes
  `IDH_SESSION_MODEL` and `IDH_SESSION_RUNTIME`. Gaze REVIEWED (same-family seat),
  verify-gate APPROVED round 1.
- The runner folds a new failing test under an open red ticket for the same
  check: `test_subagent_seat_forging_a_headless_header_takes_the_pin`, red on main
  since 2a88d52a (PR 2094, ticket 1388), opened no ticket and was found while
  isolating 1396. 1396 stays open as its carrier; logged there.
- Earlier the same day, 1386 was closed on two green records although the same
  folding had already hidden a `gaze_close` red behind it.
