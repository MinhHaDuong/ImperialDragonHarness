---
name: claude-md-is-thin-loader-idh
description: Proposing to add doctrine/posture prose to CLAUDE.md in IDH is a red flag — CLAUDE.md is a thin loader; content belongs in the scoped layers
metadata:
  type: feedback
---

Author flagged as a red flag the proposal to add an "interface posture" section
to `CLAUDE.md` (2026-07-21, agent-interface design discussion).

**Why:** In IDH, `CLAUDE.md` is deliberately a thin loader (pointers +
`@tickets/AGENTS.md`, `@RTK.md`). Doctrine lives in `rules/*.md` behind the
index with scoped injection, verified ex post by `verify-adherence`; agent
personas live in agent definition files (lazy-loaded, description-only until
spawned). Prose added to `CLAUDE.md` taxes every session of every project and
bypasses the index architecture. It also invites duplication: the batching
doctrine proposed already existed in `rules/workflow.md`.

**How to apply:** When new standing guidance is warranted, place it in the
narrowest matching layer — an existing `rules/*.md` amendment, an agent
definition body, a skill — never `CLAUDE.md`. And per the cool-down doctrine
([[feedback_harness_cooldown_stop_second_order_tooling]]), amend a rule only
against a demonstrated defect class, not a hypothetical one.
