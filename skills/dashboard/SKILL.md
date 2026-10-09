---
name: dashboard
description: "Ticket dashboard: open tickets, branches and merge requests; full state plus a delta led by the ticket count."
user-invocable: true
argument-hint:
---

# Dashboard

Read-only. Never checks out, commits, merges or launches workers: the
dashboard inspects, it does not drive the work. Steps run sequentially, each
feeding the next.

## 1. Collect

```bash
DASH_DIR="$(cd -P "$(dirname "<loaded-SKILL.md>")" && pwd -P)"
"$DASH_DIR/dashboard.sh"
```

Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for
this skill. "Read-only" means no write to the work: the fetch still updates
remote-tracking refs.

It fetches and reads `origin/main` (never the working tree), lists open
tickets with title, labels and `Blocked-by`, remote branches, open merge
requests with their auto-merge state, and recent merges.

## 2. Report

Every call prints the **full state**: one table of open tickets grouped as
in progress (branch or merge request), takeable, blocked, deferred; then the
open merge requests. The delta never replaces it.

From the second call on, put a **delta table** above the full state: changed
rows only (item | before | after), then one summary line. Unchanged state:
say so in one line, then print the full state anyway.

- **Lead the summary with the open-ticket count trend.** A good delta is a
  falling count; flag growth and name what created tickets.
- A ticket created and closed in the same merge request leaves the count
  unchanged.
- A `Blocked-by` on a closed ticket means takeable, not a stale header.

## 3. Inspect

For each merge request new or changed since the last call, read its diff,
checks and `/verify-gate` verdicts, sequentially, and report findings against
its stated claims: ticket line in path form, `ruled_tip_sha` versus the tip
(a later ticket-close commit from the merge helper is normal), test gaps,
rules relaxed. Report only; fixes belong to the session doing the work or to
the author.
