# Ticket 1499 (PR 2391): context length in tokens, sessions audit

Date: 2026-11-10, host padme. Ticket
[1499](../../../tickets/closed/1499-context-length-three-urgent-fixes.erg),
closed by PR 2391 (merge `ce587c5f6ab7ff765c633afc41d7e0327db34163`, merged
2026-11-10T08:01:02Z, read back as MERGED; reviewed head
`b1e5cf0ef6e30f7a24ec6cd54639551e0b04893f`). Writer: a coder reporting
`claude-sonnet-5-5` by its own line.

## Context

The ticket came from `design/2026-11-09-context-length-strategy.md` (PR 2365).
The author ruled on 2026-11-10, answering "defaults" to the session's
proposal, recorded on the ticket by PR 2380: note accepted for pain points 1
and 2; "context length" means the whole prompt; per-model thresholds are read
from the route skill's data; pain point 3 (a session reading its own length)
and the raid/lair criterion were cut, to be revisited once points 1 and 2
show whether overruns persist.

## Events

1. PR 2391: the status line prints the context in tokens (`prompt 211K` on a
   211,485-token fixture, `prompt ?` when the usage field is absent).
   `scripts/trace-compact-audit.py` counts sessions as well as runs, restricts
   events to its window, reports the main model, takes a threshold per model,
   defaults to the whole-prompt metric and keeps `--metric cache_read`.
   Ceilings moved into `skills/route/ceilings.json`. Tests on fixtures:
   `tests/test_statusline.py`, `tests/test_context_length_audit.py`.
2. Unreadable transcripts are reported as "COULD NOT LOOK": 2 of 10,710.
3. Review: gaze REVIEWED at `b1e5cf0e`, one self-only seat
   `anthropic/claude-sonnet-5-5`, no other family. Verify-gate APPROVED at
   round 1, session `4a72a400-3f45-4a46-a8bf-e9f148f41fcc`.
4. After the merge, another session's close-claims check printed "DROPPED:
   PR #2391 claims ticket 1499, which has no Closed: header". On the merged
   main the ticket sits in `tickets/closed/` with its `Closed:` header and the
   claim line is correct, so that read predates the merge reaching that
   checkout. Not reproduced.

## Not established

Run on 2026-11-10 with `--since 2026-11-01 --metric cache_read`, the audit
gave 278 sessions, 26 with 100+ turns, 28 at or above 230K, 4 at or above
450K, 1 at or above 550K, against the design note's 281, 28, 24, 4, 1. The
cause of the differences was not investigated; the note's scan was ad hoc.
These figures are the coder's report, not re-run in this wrap-up.
