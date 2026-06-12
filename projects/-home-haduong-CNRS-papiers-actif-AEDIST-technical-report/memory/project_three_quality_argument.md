---
name: Three-quality argument structure
description: The paper's measurement framework carves quality into data / answer / method axes; the four limits split 2/2; method quality is perpendicular, not a fifth limit.
type: project
originSessionId: e3c10d48-6444-425d-898f-f96fdc27ef2e
---
`docs/measurement-framework.md` (to be renamed `docs/argument.md`
per ticket 0147 once 0145 verifies coherence) is the paper's
conceptual spine.

**Three qualities:**

- **Data quality** — limits: Coverage (training-corpus completeness),
  Freshness (cutoff). Closed by RAG + web.
- **Answer quality** — limits: Articulation (right question framing),
  Coherence (synthesis, weak-internal). Closed by prompts + reasoning.
- **Method quality** — verifiable (citation present) / verified
  (citation actually supports claim). Closed by single-agent /
  multi-agent teams. Perpendicular to the four limits, **not a
  fifth limit.**

The F1 metric on AEDIST bundles data and answer quality into one
number; conceptually orthogonal but not separately measurable on
this fact-extraction task.

**Why:** resolved on 2026-04-30 after a discussion thread that caught
an internal inconsistency — the four limits had been called
"answer-quality" limits, but Coverage and Freshness are input-side.

**How to apply:** when discussing the paper's structure, work within
this three-quality frame. Capability stages 6–7 (general agent /
agent teams) enter the paper through *method quality*, not the
answer-quality ladder. Do not propose Closure / Embodiment /
Autonomy as a fifth answer-quality limit — the user explicitly
rejected that move in favour of treating Agent as a perpendicular
axis. The argument workflow lives in ticket chain 0145–0154.
