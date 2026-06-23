---
name: feedback_version_increment_planning
description: "Plan multi-step manuscript/prose work as shippable version increments, not waterfall phase-gates"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d9527d89-290e-4640-95bd-64bb3ccc5fa8
---

When planning a multi-step revision (e.g. journal R&R), structure it as **version
increments** (v2.0.1, v2.0.2, …), each independently shippable, NOT as a waterfall
of phase-gates. The user explicitly rejected a phase-waterfall plan in favour of a
version ladder.

Two recurring shape preferences:
- **Build the quality ratchet BEFORE the heavy content work**, so it guards every
  later edit and surfaces defects beyond the reviewer list. The ratchet = negative
  tests (defect class caught, cannot return) + positive editorial guidelines tested
  with an LLM judge. Established pattern across the user's prose projects: the AEDIST
  / Econom'IA technical report (mature model: `@pytest.mark.adherence` regex guards +
  committed ceiling files that only ratchet down + `manuscript_source` substrate +
  `docs/editorial-brief.md` + a CI test-polarity rule) and the `livre-milliards-climat`
  book proposal (lighter `check.sh` gate). Seed new ratchets from those + `config/ai-tells.yml`.
- **Author-only decisions**: the user wants me to draft 2-3 options + a recommendation +
  the one-paragraph claim each implies, then they pick. Don't decide framing for them;
  don't leave it un-drafted either.

**Why:** version increments keep each step releasable and let the user interleave;
the ratchet-first order operationalizes prose quality as tested infrastructure rather
than a manual pass (critical when reviewers flag AI-sounding prose).

**How to apply:** see [[project_oeconomia_rr_pipeline]] for the concrete ladder. Ticket
IDs are atomic — no `a/b/c` suffixes; split into new numbered tickets (now codified in
the repo's `tickets/AGENTS.md`).
