---
name: feedback_erg_close_archive
description: erg close sets the Closed header but leaves the ticket in tickets/ root; archive to closed/ at close time or /gaze flags it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7d629d57-95db-4f0c-97dc-85926c1ee6a2
---

> **PROVISIONAL** — the author plans to fold archiving into `erg close` as a
> step 4 (close would then auto-move the ticket to `tickets/closed/`). Once that
> ships, this whole lesson is obsolete: `erg close` alone will satisfy the /gaze
> gate. Delete this memory after verifying `erg close` auto-archives.

`erg close` and `erg archive` are TWO separate subcommands by design. `erg close
<id> <reason>` does three things — Closed header, log line, strip dependents'
`Blocked-by` — but does NOT move the file. `erg archive [id...]` is what moves a
Closed-headered ticket to `tickets/closed/` (it skips a ticket still referenced
by an open Blocked-by). The archive help says it outright: "Run erg close ID
REASON before archiving." `erg-pr-merge` runs both (close then `$ERG archive`) at
merge time.

The trap: `/gaze` runs BEFORE merge, so a manually-closed-but-unarchived ticket
left in `tickets/` root trips its gate (0149, PR #827, 2026-06-23 — burned a
round; the fix agent moved it).

**Why:** the close-and-archive convention is enforced at the /gaze gate; closing
alone is not enough because the archive normally only happens at erg-pr-merge,
which is too late.

**How to apply:** when closing a ticket on the branch ahead of the PR, run the
full sequence — staging TWICE, because `erg archive` physically moves the file
AFTER the first `git add -u` (skipping the second left a stale
tracked-but-absent blob on main, ticket 0264 / PR #1044, fixed #1046):
```bash
tickets/erg close <ID> <reason>
git add -u tickets/                    # stage the Closed: header edit
tickets/erg archive tickets/ | sed -n 's#^ARCHIVED #tickets/closed/#p' | xargs -r git add --
git add -u tickets/                    # stage the deletion of the OLD path — easy to skip
git status --porcelain tickets/        # no bare M/D at the old path, only the closed/ add
```
Never dismiss a pre-commit "cannot open <file>" warning during a ticket close
as benign without checking for a stray tracked-but-absent path. See
[[feedback_verify_deferral_tracker]].
(Absorbed feedback_erg_close_archive_staging_order, dream 2026-07-22.)
