---
name: feedback_check_sibling_tickets_before_reorg
description: "before executing a cross-repo file move/reorg the user just approved via a quick choice, check sibling-project tickets for a prior documented decision on the same question"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c40a15a0-a05a-4167-aa8f-6b7351eb49a6
---

When a user flags something as looking misplaced ("seems unrelated!") and,
offered a quick multiple-choice on what to do, picks the more drastic option
(e.g. "move it to the other repo") — pause and check whether a prior,
independent decision on that exact question already exists before executing.

**Why:** 2026-07-07, `climate-finance-het`: the user questioned why a
citation-figure pipeline for a *different* paper lived in this repo. Asked
"leave / move / leave-as-is", they picked "move it to polycentric_activity".
Before starting the move, a check of that sibling repo's own tickets found
one (`polycentric_activity` ticket 0027) — authored by the same user, same
day — that already recorded the opposite as a deliberate call: keep the
machinery here specifically to avoid duplicating it there. Surfacing that
before touching any files let the user reconcile in one round-trip instead
of after a real cross-repo migration was underway.

**How to apply:** Before executing a reorg/move that spans repos or
undoes something another artifact (ticket, PR, architecture note) already
addressed, spend one search pass on the *other* side of the boundary —
sibling repo's tickets, the original PR body, related architecture docs —
for an existing decision. If found, present the conflict and let the user
reconcile before acting, rather than either silently overriding it or
silently deferring to the multiple-choice answer alone. This is cheap
(one grep/read) relative to the cost of a wrong structural change.
