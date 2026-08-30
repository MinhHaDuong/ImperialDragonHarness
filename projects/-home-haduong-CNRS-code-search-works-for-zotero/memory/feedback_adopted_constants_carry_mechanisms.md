---
name: feedback-adopted-constants-carry-mechanisms
description: A constant copied from upstream arrives without the mechanism that made it safe — read the source, not the summary, and check what guards the number
metadata:
  type: feedback
---

When adopting a value from another project, read the code that uses it, not
a summary of it. A constant copied out of its context arrives without the
logic that made it correct, and the citation ("adopted verbatim", "X's own
geometry") then asserts a fidelity that does not exist.

**Why:** on 2026-08-29 this project had adopted Zotero's `CHUNK_MAX_TOKENS =
768` as its chunk size. Upstream uses it as a **ceiling inside a `min()`**
against the live model's window — its own comment says "a ceiling rather than
a target" — with a second cap dropping the heading path when it would exceed
a quarter of the budget. The number was copied; the two caps and the drop rule
were not. Result: a design that would silently truncate 60,6% of the corpus's
text mass at embed time, while claiming to follow the platform.

A roar sweep then found the defect was a class, not an incident: **four of
eight** claims the specification made about upstream behaviour were wrong.

**How to apply:** for any value taken from another codebase, fetch the file at
a pinned SHA (`gh api repos/<o>/<r>/contents/<path>?ref=<sha>`) and read what
surrounds the constant — what caps it, what subtracts from it, what drops when
it is exceeded. Record the coordinate (file, line, SHA) beside the claim, since
a draft PR moves and a verification is only valid at the commit it was read at.
Prefer the word "unverified" over silence when you could not check: a grep that
misses is not a refutation.

Two shapes to watch for specifically. A constant that is a **bound** rather
than a **target** — the tell is that it never binds under current
configuration, which makes it look like dead config when it is actually a
guard against a future case. And a **guard that drops rather than truncates**
— cheap to omit in reimplementation and invisible until the pathological input
arrives.

Related: [[feedback-preserve-agent-output]].
