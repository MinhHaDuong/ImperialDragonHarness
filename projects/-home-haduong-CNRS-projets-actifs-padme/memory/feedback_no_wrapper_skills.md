---
name: no-wrapper-skills-for-cli-tools
description: "Don't create/keep skills that merely wrap a self-documenting CLI — instructions in CLAUDE.md suffice for the model to call the tool directly"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 327d71bf-21b9-4042-9f61-6851340154c2
---

When a skill would be a thin delegation to a self-documenting CLI (e.g. `tickets/erg` with `--help --all`), the user wants NO skill at all: a few lines in CLAUDE.md naming the direct invocations is the whole interface. Stated 2026-06-06 after PR #6 rewrote three ticket wrapper skills that PR #7 then deleted ("/ticket-new, /ticket-ready, /ticket-close should not exist at all. Our instructions should be sufficient so that the smart model do erg new, erg ready and erg close.").

**Why:** KISS — a wrapper skill adds an indirection layer to maintain (it drifted badly once: v1-era skills survived two format generations), and the model reads `--help` as easily as skill text.

**How to apply:** Before writing or rewriting a skill, ask: does it add logic beyond invoking one tool? If not, document the direct invocation in CLAUDE.md instead, and propose deleting any existing wrapper. Skills are for multi-step orchestration, not command aliasing. See [[padme monitoring architecture]] for the user's broader KISS stance.
