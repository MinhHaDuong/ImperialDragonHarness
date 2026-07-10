---
name: feedback_pilot_one_instance_critiques_the_ticket
description: "Before building a compute_*.py analysis from a ticket spec, pilot one instance read-only — it can falsify the ticket's design, not just preview the data"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9ada6bf5-ae0f-4fdd-be7d-85cf0f47ae0b
---

Before building the analysis machinery a "compute_X" ticket asks for, run a
read-only pilot on **one** instance and let it critique the ticket's design, not
just preview a number.

**Why:** Ticket 0166 asked for a six-term grey-vs-academic lead-lag table with a
segment rule already specified (grey = `from_grey`). A single-term pilot
(de-risking, 2026-07-09) showed the `from_grey` flag captures 0.7% of the corpus
and is blind to the early institutional documents where instruments first appear
(OpenAlex indexes them as academic). The ticket's *segment definition was the
defect* — invisible until a term was actually run. Building the script first
would have produced a clean, tested, wrong table. The pilot converted a risky
quantitative claim into a safe narrative one and surfaced a spun-out paper
([[project_paper_instrument_circulation]]) — for the cost of one query.

**How to apply:** For any Phase-2 compute ticket, before writing the script or
its test, load the real corpus and run the proposed method on the smallest
meaningful slice. Ask not "what's the number" but "does the ticket's segment /
threshold / match rule survive contact with the data?" Report a design blocker
back to the ticket if it doesn't. Relates to [[feedback_manuscript_number_provenance]]
(trust only traceable numbers) and the pilot-before-build reflex.
