---
name: Braindump / imagine mode signals design dialogue
description: When user says "braindump" or "imagine mode", engage as a design partner — reflect, sharpen, ask — without writing docs until they ratify
type: feedback
originSessionId: 7bdc6f84-5a5f-4006-8e2b-c4190eecb4c0
---
When the user opens a thread with "Braindump," "Imagine mode," or similar, they are signalling a design-exploration session. The right behavior is to reflect what they said back structurally, name the load-bearing ideas, and ask 2–4 sharpening questions that surface the decisions they still need to make. Do **not** commit the braindump into docs (MASTERPLAN, tickets, memory) until they explicitly ratify the direction.

**Why:** Author pattern, session 2026-04-17 on the v0 fusion pipeline. The user was exploring a multi-stage design (incrementality, information fusion taxonomy, sidecar + invariants, 3-tier verification, HITL memory). Committing intermediate ideas would have locked in framings that later iterations refined. The dialogue pattern kept the design space open until the decisions were made.

**How to apply:** Hold back writes. Keep responses dense and dialog-oriented. Use headers + tables + bullet lists to show the structure of *their* idea, not yours. Propose concrete shapes (e.g. "sidecar vs long table") and trade-offs, then let them pick. Annotate decisions in docs/tickets *only after* the user says "commit," "annotate," "file it," or equivalent.
