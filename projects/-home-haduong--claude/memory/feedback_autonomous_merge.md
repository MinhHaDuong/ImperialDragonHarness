---
name: Autonomous merge for trivial ticket housework
description: Trivial ticket housework PRs (renames, decollisions, log fixes) may be merged without asking the user first
type: feedback
originSessionId: 6443cf93-df9d-409c-bc74-bce8772c384b
---
Trivial ticket housework is allowed autonomous merge — no need to ask the user for confirmation.

**Why:** These changes (ticket renames, ID decollisions, log section fixes) carry no risk and asking adds friction.

**How to apply:** PRs whose entire diff is ticket file renaming or metadata corrections (no code, no skill logic, no beat.py) can be merged immediately after opening, without prompting the user.
