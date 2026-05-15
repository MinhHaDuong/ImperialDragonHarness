---
name: Use @-includes in CLAUDE.md for critical format rules
description: Prose references to docs don't guarantee subagents read them — @-includes inject content automatically
type: feedback
originSessionId: a1353f97-2f64-4cef-8836-b76517787f40
---
Prose like "see tickets/AGENTS.md for format rules" is ignored by subagents that don't proactively read CLAUDE.md. Use `@tickets/AGENTS.md` (direct @-include) instead — it injects the file into every agent's session context at startup.

**Why:** During the 2026-05-08 raid, verify-gate agents had a stale `tickets.md` in `.claude/rules/` that still documented `Status:` as required. This caused 4 false REROLL/ESCALATE verdicts on valid `Closed:` headers. Fix: remove stale rules files, add `@tickets/AGENTS.md` to CLAUDE.md so the accurate spec is always in context.

**How to apply:** Any time a rule or format spec must be known by all agents (ticket format, import order, data directory conventions), use an @-include in `.claude/CLAUDE.md` rather than a prose pointer. Check that the referenced file is the authoritative source (co-located with the artifacts it describes is a good sign).
