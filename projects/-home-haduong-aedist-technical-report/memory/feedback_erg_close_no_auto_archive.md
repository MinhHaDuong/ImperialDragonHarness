---
name: feedback-erg-close-no-auto-archive
description: "erg close writes the Closed: header but does NOT git-mv the file into tickets/closed/; erg check then warns"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0260a84d-76b1-4100-aa48-b690ff582478
---

The current `tickets/erg` binary's `erg close <id> "<reason>"` writes the
`Closed:` header and appends a close log entry, but does **not** move the file
into `tickets/closed/`. `erg check` then emits a (non-fatal) warning:
`WARN <ticket>: closed ticket not in closed/ directory`. Warnings accumulate
silently — 7 had piled up by 2026-06-09 (0482-0488 + 0492).

**Why:** contradicts the older memory note "erg auto-archives to tickets/closed/"
— that behaviour is not present in this binary version. Do not assume `erg close`
relocates the file.

**How to apply:** after `erg close`, `git mv tickets/<id>-*.erg tickets/closed/`
in the same commit so `erg check` stays at 0 warnings. Or batch-archive
periodically: `for t in <ids>; do git mv tickets/$t-*.erg tickets/closed/; done`
then re-run `./tickets/erg check tickets/` to confirm PASS with 0 warnings.
Pairs with [[feedback_auto_merge_bypasses_ticket_close]] (the merge side of the
same close-hygiene gap). See [[project_erg_closed_dir]].
