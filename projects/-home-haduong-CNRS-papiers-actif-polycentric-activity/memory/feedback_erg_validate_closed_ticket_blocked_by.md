---
name: feedback-erg-validate-closed-ticket-blocked-by
description: erg's pre-commit hook validates a single tickets/closed/*.erg file in isolation and can't resolve Blocked-by refs to siblings still in tickets/ — strip Blocked-by lines from a ticket before/while closing it if its blockers are still open.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc2349a2-725b-4756-8875-771442f0f763
---

`erg-pr-merge` (2026-07-07, ticket 0014) closed and archived a ticket whose
header still had `Blocked-by: 0012` / `Blocked-by: 0013` (both still open —
the ticket's substance was done even though the formal blockers weren't
closed yet). The commit's pre-commit hook then failed:
`Blocked-by '0012' references unknown ticket ID`, even though
`tickets/0012-*.erg` and `tickets/0013-*.erg` both existed and a full
`erg check tickets` on the whole corpus passed clean. Only `erg validate
tickets/closed/0014-*.erg` (single-file, file already moved to `closed/`)
reproduced the error — the per-file validator did not resolve `local-ref`
Blocked-by targets against the tickets/ store root once the referencing
file itself lived under `tickets/closed/`.

**Why:** the failure only shows up on the single-file path taken by a
commit hook right after `erg archive`, not on the corpus-level check most
sessions run to sanity-check ticket edits — easy to be surprised by a
git-hook rejection after `erg check` already said PASS.

**How to apply:** per `erg spec`, `Blocked-by` is meant to be removed once
the dependency is resolved anyway ("remove the line once the dependency is
resolved"). When closing a ticket whose blockers are still open in
substance-only terms, remove its `Blocked-by:` lines as part of the close
edit (with a one-line log note explaining why) rather than leaving them —
this is both spec-correct and sidesteps the validator quirk. Log entries
must stay single-line (`YYYY-MM-DDTHH:MMZ author verb detail`); a wrapped
multi-line note triggers a separate "malformed log line" validation error.
