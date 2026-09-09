---
name: reference-rules-tree-is-resident
description: "The whole rules/ tree arrives in the system prompt as global instructions — 28 590 tokens, 73% of the resident budget; the pointer-table design is void"
metadata: 
  node_type: memory
  type: reference
  originSessionId: aceca52d-6c71-4a74-ae75-85a9b713e441
  modified: 2026-09-09T16:39:09.862Z
---

Observed 2026-09-09, in the session's own context: **18 of the 19 rule bodies**
under `~/.claude/rules/` are present in full in the system prompt, labelled
"user's private global instructions for all projects". Only `state.md` was
absent. Neither `CLAUDE.md` (which imports only `tickets/AGENTS.md` and
`RTK.md`) nor `on-start.sh` (7 752 bytes, the rules README alone) injects them.
**The cause was not isolated** — presumably a runtime auto-load of the directory
— so treat this as an observation with a date, not a settled mechanism, and
re-check it before acting on it.

Measured consequences:

- Resident cost per session is ~39 200 tokens before the first question, of
  which **rules are 28 590 (73%)**. `workflow.md` (7 937) and `git.md` (6 091)
  are 14 028 between them.
- `rules/README.md` presents itself as a pointer table whose bodies are "read on
  demand". Nothing reads them on demand: over 101 days and 5 730 sessions,
  `workflow.md` was opened **50 times** and `git.md` 23 — because they are
  already there.
- `inject_rule_on_edit.py` re-injected **1 069 rule bodies** in that window, all
  already resident. Verified live: `coding-python.md` was in the system prompt
  and the hook served it again in full on the first Python `Write`.

Why it matters for the multi-agent port: on a runtime without that auto-load,
28 590 tokens must either be re-injected by an adapter or become genuinely
on-demand. That is the real prerequisite behind ticket 0572, not a tidying
preference. Numbers and method: `scripts/census/`, `HANDOFF-2026-09-09.md`.
