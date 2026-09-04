---
name: feedback-erg-log-stamp-must-match-wall-clock
description: "A ticket log entry's timestamp must match the real wall clock at write time, not an estimate — bench/check_ticket_logs.py fails on a stamp that postdates the commit that wrote it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dc5e15a4-edc1-4528-b6bf-d9afd95441c1
  modified: 2026-09-04T09:07:31.883Z
---

When appending a ticket log entry by hand (writing the `YYYY-MM-DDTHH:MMZ`
prefix directly, or trusting `erg close`'s auto-generated one), check the
actual current time first (`date -u +"%Y-%m-%dT%H:%MZ"`) rather than
estimating or reusing a nearby timestamp from earlier in the session.

**Why:** `bench/check_ticket_logs.py` (this repo's ticket-log gate, part of
`make check`/`make lint`) fails any entry whose stamp is *after* the commit
that actually wrote it — the check reads the entry's own claimed time
against `git log` on the commit carrying that line. A guessed or
copy-pasted-from-earlier stamp drifts ahead of real time easily in a long
session with many parallel tool calls between "I know what to write" and
"I actually commit it."

**How to apply:** run the date command immediately before writing the log
line, not once at the start of a work block. Caught three instances of this
exact defect in one session (2026-09-04): one pre-existing on `main`
(ticket 0640, someone else's entry, ~9 minutes off) and two of this
session's own (also ~9 minutes off, from writing the timestamp before
finishing the surrounding work rather than at actual commit time). The fix
is mechanical — correct the stamp to the commit's own time — but only if
caught; nothing else in the normal workflow surfaces this until the gate
runs.
