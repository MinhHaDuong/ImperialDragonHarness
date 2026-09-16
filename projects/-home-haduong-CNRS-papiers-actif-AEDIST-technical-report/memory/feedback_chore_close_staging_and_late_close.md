---
name: feedback-chore-close-staging-and-late-close
description: erg close + git mv stages pre-edit content (Closed header lost); hunts may close tickets in late review rounds — re-check before chore-closing
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0a31bfb1-e15a-4b7f-8254-b4e0c65fde11
---

Two chore-close traps from the 2026-06-12 hunt-gating session:

1. `erg close ID reason && git mv tickets/X tickets/closed/` stages the
   file content as it was at `mv` time — but the commit then picked up
   only the rename, NOT the `Closed:` header edit (rename 100%,
   0 insertions). The header sat unstaged in the working tree.
2. A hunt/raid session may close+archive its ticket in a LATE review
   round (0551 did in round 2, after my files-list snapshot showed no
   ticket change). `erg close` then bounces "no ticket found".

**Why:** #1008 shipped without the Closed header until caught and
amended; an unnecessary 0551 chore-close was attempted.

**How to apply:** after `erg close`, always `git add` the archived file
explicitly before committing (`git mv` alone is not enough when erg
edited the file in the same compound). And before chore-closing a
ticket for a merged PR, re-pull and check `tickets/closed/` first — the
PR may have closed it in a late push. Related: [[feedback-auto-merge-bypasses-ticket-close]].
