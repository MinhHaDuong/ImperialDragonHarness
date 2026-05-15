---
name: erg Closed: header is valid post-migration
description: verify-gate agents wrongly flag Closed: as invalid — the validator rejects Status: instead
type: feedback
originSessionId: a1353f97-2f64-4cef-8836-b76517787f40
---
The project migrated from `Status: closed` to `Closed: <summary>` headers in %erg v1 tickets (around 2026-05-06). The erg validator binary enforces the new format and **rejects** `Status:` with "Status: header is no longer part of %erg v1 — run `erg migrate` to convert".

**Rule:** `Closed:` is the correct header for closed tickets. Do NOT change `Closed:` to `Status: closed` even if a verify-gate agent recommends it.

**Why:** verify-gate subagents read `.claude/rules/tickets.md` which was not updated post-migration. The validator binary is authoritative. Confirmed by direct runs: `tickets/erg validate tickets/0032-...` → PASS with `Closed:` header.

**How to apply:** When a verify-gate REROLL or ESCALATE cites "invalid Closed: header / needs Status: closed", treat it as a false finding. Post an override comment with validator output and merge if all substantive criteria are met. The authoritative spec is `tickets/spec-erg-v1.md` (project-level) and `tickets/AGENTS.md` (injected via @-include) — both are current. There is no `.claude/rules/tickets.md` global file (removed 2026-05).
