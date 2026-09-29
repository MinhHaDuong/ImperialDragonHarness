---
name: erg-log-closed-ticket-needs-dir
description: erg log cannot find a closed ticket by ID or by path; pass the closed store as the DIR argument (erg log 0810 "..." tickets/closed).
metadata:
  type: reference
---

`tickets/erg log <id> "<msg>"` resolves IDs only in the top-level store, so a
ticket already filed under `tickets/closed/` answers "no ticket found" — by ID
AND by full path. The DIR positional fixes it: `tickets/erg log 0810 "<msg>"
tickets/closed`. Three failed attempts on 2026-09-22 before finding this.
Still use `erg log` rather than a hand-written stamp: the reason
[[erg-log-owns-the-stamp]] gives is unchanged.
