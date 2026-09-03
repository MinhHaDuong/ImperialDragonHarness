---
name: feedback_mechanism_wearing_a_requirements_number
description: "Normative text that names a mechanism cannot be asserted; three failed assertions is the measurement that proves it, not an argument"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 23ae8345-4e0c-469c-8519-4d269f82e902
  modified: 2026-09-03T11:01:39.111Z
---

A requirement or constraint must name a **property**, never an implementation.
Two instances fell in one afternoon (2026-09-03) and both were the author's
catch, not mine.

- **R31** — "a configuration MUST prove it works on my machine before it is
  used" — read to him as *"it should work as it says"*. Retired.
- **C4** — titled *status answers from counters*, body forbidding "scanning a
  table a stage is writing" — read as the same thing applied to the
  configuration subsystem. Dissolved into an R17 clause.

**Why:** the tell is mechanical and cheap. Compare a section's titles against
its own definition — §4 is defined to hold *facts*, and C1/C2/C3 each named a
fact while C4 named a build. And the decisive evidence is not an argument at
all: **three assertions were written for R31 and each was withdrawn because its
only reachable red belonged to a neighbour (R10).** A requirement whose every
falsifier is another requirement's has no extension of its own — the
apparatus test run as a measurement, returning the same answer three times.
That is what convinced, where prose about "promise vs apparatus" had not.

**How to apply:** when a clause resists assertion, suspect the clause before the
harness. Ask what a user could *observe* — here it was speed, which converted an
unassertable prohibition into a testable promise. Then check the residue has a
real owner: dissolving C4 was safe only because R17 already carried the
work-account property mechanism-free, and the piece nobody owned had to be
filed as its own ticket (0611) rather than asserted into an existing number.
Beware the argument that proves too much: I justified C4's removal partly by its
stray MUST, and review found C1 carries one too. See
[[feedback_verify_the_load_bearing_claim]] and
[[feedback_probe_needs_discriminating_control]].
