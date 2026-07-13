---
name: pin-intervention-surface-to-measured-window
description: "Before pinning an A/B intervention on a skill behavior, git-log the surface to check what was live during the measured baseline window — the obvious surface may already implement the \"treatment\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f12048a3-94f8-4989-b3f6-9bcad58fd9b0
---

Raid 291-245 (2026-07-13), ticket 0315: the planner proposed flagging gaze's
internal REROLL round-1 branch as the convergence intervention — but `git log -L`
showed that branch was already gate-only during the June measurement window, so
`enabled: false` would either be a no-op flag or silently revert live behavior.
The $259/wk vg-bucket cost comes from caller-level re-invocation of full /gaze,
which is where the flag landed.

**Why:** a cost measured on a window attributes to the behavior live in that
window. Pinning the intervention to a surface that changed since (or that
already implements the treatment) produces an A/B that measures nothing or
regresses production as its "control".

**How to apply:** when pre-registering any A/B on skill/prompt behavior, first
`git log -L <lines>:<file>` the intervention surface and confirm which arm the
measured window actually ran. The control arm must equal the measured baseline
behavior; if the surface already implements the treatment, look one level up
(caller, re-invocation, orchestration) for where the measured cost really
accrues. See [[verify-fork-under-execution]] for the sibling lesson on gaze
fork completion markers.
