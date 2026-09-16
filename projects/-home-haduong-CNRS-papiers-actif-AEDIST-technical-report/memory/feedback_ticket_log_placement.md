---
name: Ticket log entries go in the log section, not at EOF
description: Agents append log entries at end-of-file which lands in the body section; they must be inserted before originSessionId: ffa4fcd3-10b8-4ca3-9f40-aea04d4166a7
---
body --- separator
type: feedback
---

Log entries (claimed, status, note, bump) must appear between `--- log ---` and `--- body ---`. Appending at EOF places them in the body section.

**Why:** Celebrate sweep after namespace audit (2026-04-24) found 15+ tickets with log entries in body section. Ticket 0127 added a validator (PR #292) but it checks format, not placement — agents still need to know WHERE to insert.

**How to apply:** When claiming or updating a ticket, locate the `--- body ---` line and insert the new log line immediately *before* it (or after other existing log lines in the log section). Never append at EOF.
