---
name: read-the-ticket-log-not-the-body
description: "An .erg log is append-only and always newer than the body; a long investigation's body drifts behind its own log, so read the log before acting on a ticket's Actions or mechanism."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 051c3e4f-eff5-4c4a-95a6-ebdb65d927df
  modified: 2026-09-11T16:09:14.025Z
---

**Read a ticket's log before acting on its body.** An `.erg` file pairs an
append-only log with a mutable body. The log is therefore always the newer of
the two, and nothing makes the body follow it. The longer and more valuable the
investigation, the further apart they drift.

**Why:** on 2026-09-11 I read ticket 0727's body, and recommended to the author
that he run its Action 1 as the cheap way to unblock the sitter release. Wrong
twice, and both corrections were already in that ticket's own log, five days
old. `update_url` is REQUIRED — the build Action 1 asks for is refused at
install, established with a control. And the mechanism Action 1 isolates was
refuted the same evening: the fix built on it shipped and died on the identical
schedule, and the timing never fitted (`extensions.update.interval` is a daily
86400 against a disable twenty seconds after install). The recommendation went
to the author before I had read the log.

**How to apply:** before quoting a ticket's mechanism, Actions, or Test section
— especially to recommend work — read its log tail first, and grep the log for
`REFUTED|NOT SUPPORTED|superseded|is wrong as stated`. A body section titled
"The mechanism this points at" is a hypothesis as filed, not a finding. Where
the body is stale, correct it with a short section ahead of the filed text
naming the supersessions, mark refuted Actions void and leave them unstruck —
deleting a refuted arm is how it gets proposed again.

The class is filed as ticket 0768 with four further candidates (0025, 0491,
0606, 0722), swept with a positive control. Related:
[[verify_the_load_bearing_claim]], [[a_stale_artifact_reads_as_live]],
[[matching_a_stale_number_is_not_confirmation]].
