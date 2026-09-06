---
name: ticket-log-stamps-are-utc
description: "check_ticket_logs compares an erg log stamp against UTC while the session's date banner shows local time (+2); never hand-write a stamp"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c237237f-abd3-4b9c-94b8-0f98e597a30a
  modified: 2026-09-06T22:09:16.569Z
---

`bench/check_ticket_logs.py` fails any `--- log ---` entry stamped later than the commit that wrote it, and for an uncommitted file it compares against the clock — in **UTC**. It bounced `make check` three times in one session on 2026-09-06 because I typed plausible-looking stamps ahead of the clock, the last time because the harness announced "today is 2026-09-07" (local, +2) while UTC was still 22:05 on the 6th.

**Why:** the session banner and the gate use different clocks, so a stamp that matches the banner can be two hours in the future by the gate's reckoning. The failure is cheap but it costs a full `make check` cycle each time (~60-85 s plus the guards).

**How to apply:** let `erg log <ID> "note …"` write the stamp — it stamps correctly. When editing a log line by hand, take the value from `date -u +%Y-%m-%dT%H:%MZ` in the same turn, never from the date banner or from memory. Related: [[spec-edit-mechanics]], [[rerun-gate-after-own-fix]].
