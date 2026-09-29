---
name: feedback_hand_delegates_literal_paths
description: Instructions to a delegate carry resolved literal paths (tickets/0983-launch-time-link-validator-that-fails-lo.erg), never patterns like tickets/0983-<slug>.erg or tickets/0986-*.erg
metadata:
  type: feedback
---

2026-09-29: relaying fixes to the 0983 hunt agent, I wrote
`**Ticket:** tickets/0983-<slug>.erg` and `tickets/0986-*.erg`. The author
interrupted: "Use a literal path." A pattern hands the delegate a resolution
step it may do differently, or copy verbatim — `erg-pr-merge` parses the close
claim literally, and an unresolved `<slug>` bounces the merge. The same day a
reviewer was launched with the literal prompt "PLACEHOLDER": templates that
reach a delegate unfilled are one failure class.

**How to apply:** `ls tickets/ | grep ^NNNN-` (or the equivalent) before
writing the message, and paste the result. Applies to file paths, branch
names, PR numbers and commands alike.
