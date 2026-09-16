---
name: Raid budget failure recovery
description: When a raid hits budget mid-migration, check locked worktrees for uncommitted work before redesigning the ticket
type: feedback
originSessionId: b242a158-a8c5-47f4-a4af-d68efdd25967
---
When a raid reports budget exhaustion on a large ticket, the first step is to inspect the locked worktree (`git worktree list`, then `git -C <path> diff HEAD --stat`). Uncommitted work there may be nearly complete — the agent ran out of budget before committing, not before working.

**Why:** The 0156 raid completed the entire models.yaml migration (52 entries) and started Python changes but hit budget before committing. Investigation found the work intact. Recovery: extract completed files, add a backward-compat shim for the half-migrated callers, and split the remaining work into a new ticket (0161).

**How to apply:** On any "budget exhaustion" failure for a large ticket:
1. `git worktree list` — find the locked worktree for that ticket
2. `git -C <worktree> diff HEAD --stat` — see what's done but uncommitted
3. If substantial: salvage the complete parts, add shims for partial parts, create a follow-up ticket for the remainder
4. If nothing: the ticket was too large from the start — split it before retrying
