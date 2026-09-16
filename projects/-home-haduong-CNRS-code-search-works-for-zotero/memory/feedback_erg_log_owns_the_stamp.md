---
name: feedback-erg-log-owns-the-stamp
description: "Append ticket log lines with `erg log ID LINE`, never by hand — the tool owns the UTC stamp."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: af8462f8-814a-41dd-8e1e-b4beb1839a7a
  modified: 2026-09-15T21:14:00.474Z
---

`tickets/erg log ID LINE` prepends the current UTC stamp itself, inserts the
entry just before `--- body ---`, and `erg validate` rule 11 enforces the shape.
Hand-writing the line means guessing the clock.

**Why:** on 2026-09-15 I hand-wrote two log entries in one evening and guessed
both stamps wrong — 20:05Z when it was 19:53Z, then 20:45Z when it was 20:34Z.
`make ticket-logs` caught both ("none stamped after the commit that wrote it"),
so nothing shipped, but each cost a fix-and-rerun cycle. The author asked whether
the stamp could be delegated to git-erg. It already could; I had never looked at
`erg --help`.

**How to apply:** `./tickets/erg log NNNN "claude note …"` for every log append.
The first token is the actor and the second a verb by convention. Reach for
`erg --help` before hand-editing any `.erg` file — `new`, `close`, `label` and
`archive` own their mechanics the same way, and `erg new` additionally allocates
the ID race-safely. The general form: when a repo ships a binary for a file
format, the format's invariants live in the binary, and hand-editing re-derives
them from memory. Related: [[feedback-erg-log-stamp-must-match-wall-clock]],
[[feedback-ticket-log-stamps-are-utc]].
