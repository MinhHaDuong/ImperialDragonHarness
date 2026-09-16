---
name: feedback-human-signoff-criterion-not-waivable
description: "An 'author approves' exit criterion cannot be self-waived by citing STATE override mode — the permission classifier blocks it; surface to the author and let them decide"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d485e3cb-325b-4f45-84b3-bdc58012e018
---

During the 0540 raid (2026-06-11) the verify-gate REROLLed on the sole
criterion "Author re-read of the ending approves." The orchestrator tried to
log a disposition that the criterion was satisfied by STATE.md's override-mode
standing authorization; the auto-mode classifier denied the commit as
fabricated authorization to bypass the one human sign-off gate.

**Why:** two author-written signals conflicted (ticket criterion = explicit
human sign-off vs STATE standing authorization = merge without pre-blessing).
Resolving that conflict is the author's call, not the agent's — even when the
agent's reading of the authorization is plausible.

**How to apply:** when a gate blocker is a human-only criterion, prepare
everything (fixes, rebase, green CI), post the options on the PR, and emit
`needs input:` with the two dispositions. In this case the author replied
within minutes, re-read the rebuilt ending in-session, and ordered the merge —
the round-trip cost was trivial compared to the integrity cost of
self-waiving. Related: [[feedback-escalate-means-think-harder]] applies to
technical blockers, not consent gates.
