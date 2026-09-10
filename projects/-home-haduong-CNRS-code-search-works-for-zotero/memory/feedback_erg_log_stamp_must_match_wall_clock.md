---
name: feedback-erg-log-stamp-must-match-wall-clock
description: "A ticket log entry's timestamp must be read in the SAME tool call that writes it — bench/check_ticket_logs.py fails a stamp postdating the commit, and reading the clock at the top of a work block is not close enough"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dc5e15a4-edc1-4528-b6bf-d9afd95441c1
  modified: 2026-09-10T10:35:47.606Z
---

Read the clock **in the same tool call that writes the log line**
(`date -u +"%Y-%m-%dT%H:%MZ"` and the write, one call). Not once per work
block, not "shortly before" — the same call.

**Why:** `bench/check_ticket_logs.py` (part of `make check`) fails any entry
whose stamp is *after* the commit that wrote it, reading the claimed time
against `git log` on the carrying commit. Minutes pass between "I know what to
write" and "I commit it", and a stamp typed to read plausibly drifts ahead.

**How to apply:** the clock read and the write are one call. And on **any**
branch touching `tickets/`, run `python3 bench/check_ticket_logs.py` before
pushing — it is seconds, and it is the only thing that surfaces this.

**Recurrence, 2026-09-10, worse than the 2026-09-04 original.** Three stamps
invented in one session, in two separate rounds:

1. Two on the branch filing tickets 0763/0764 — 09:52Z and 09:56Z on a commit
   written at 09:47:08Z. `erg check` passed (it does not read stamps) and I
   never ran `make check` on that branch, so it reached an open PR. A Sonnet
   reviewer ran the gate and found it.
2. Then, **while correcting them**, a third: 10:34Z written when the clock said
   10:23Z. The gate caught that one immediately.

Two things this adds to the 2026-09-04 entry. First, the failure is not "forgot
to check the time" — I had run `date -u` earlier in both rounds and reused the
value after the work drifted past it; that is why the rule is now same-call, not
check-first. Second, the branch I skipped the gate on was the **filing PR for
0763, the ticket about gates nothing runs.** See [[project-search-works-has-no-ci]]:
in this repo a hand-run `make check` is the only backstop, so skipping it on a
ticket branch has no second line of defence.

Related: [[feedback-ticket-log-stamps-are-utc]] (the banner shows local +2),
[[feedback-rerun-gate-after-own-fix]].
