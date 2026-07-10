---
name: feedback-propagate-notes-to-tickets
description: "Session notes that assign inputs to tickets (\"alimente 0137\") must be written INTO those tickets at once; Execute agents start cold from the ticket file alone"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 62b257a5-ee6e-4162-b241-419038383cd8
---

The Vannes notes (2026-07-07) assigned inputs to tickets 0135/0137/0141/0143
("alimente X") and diagnosed the conclusion as the priority worksite — but no
ticket was updated and no conclusion ticket existed. The user caught it with
"On a bien intégré les notes de Vannes dans le workplan ?" (answer: only half).

**Why:** Execute runs in a fresh context; the ticket body is the only input.
A pointer that lives in a notes file is invisible to the agent that does the
work. Same for sequencing: a plan step described in a decision ticket (0165's
"translate the VF") is not owned work until a ticket executes it — check that
every step of an adopted plan has an owning ticket.

**How to apply:** when a debrief/decision session routes material to tickets,
append an "Input from …" section to each target ticket body in the same PR as
the notes. Encode ordering in the DAG (Blocked-by), e.g. manuscript children
blocked by the base-rebuild ticket 0172 so the autonomous stream cannot edit
superseded text. Related: [[feedback_decide_dont_micromanage]].
