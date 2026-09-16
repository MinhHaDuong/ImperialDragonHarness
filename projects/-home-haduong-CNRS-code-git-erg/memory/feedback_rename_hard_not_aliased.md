---
name: feedback_rename_hard_not_aliased
description: "erg header/command renames are hard renames + \"run erg migrate\" hint, never deprecated aliases"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1c825fe-8065-4dc5-bf57-fbc55df60426
---

In git-erg, renaming a header or command is a **hard rename**: the old form
becomes an error pointing to `erg migrate`, not a deprecated alias. Confirmed by
the author for ticket 0175 (Tag→Label), overriding the ticket's own
alias-with-stderr-notice wording.

**Why:** Every prior rename follows this pattern — `Status:`→`Closed:` and
`Tags:`→`Tag:` both hard-reject with "run `erg migrate` to convert" (erg.go).
The only alias in the codebase is `ls`→`list` (permanent, silent). Deprecation
scaffolding (stderr notices, dual config-key read, "drop after one release") has
no precedent here and is YAGNI.

**How to apply:** For a rename, update the parser to reject the old key with a
migrate hint, add a rewrite pass to `erg migrate`, and update the dispatch table
directly. No backward-compat alias. The "don't rename config key in same commit"
sequencing concern dissolves because `erg migrate` rewrites config text-level
with no `loadConfig()` dependency.
