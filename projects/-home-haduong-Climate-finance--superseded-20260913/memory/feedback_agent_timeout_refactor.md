---
name: Agent timeout on refactor step
description: Worktree agents exhaust budget mid-refactor — provide pre-written code and narrow scope
type: feedback
originSessionId: 4fce2fc5-8792-42cb-b9a6-0a6fe78418d1
---
Agents consistently run out of time during the refactor TDD step, leaving uncommitted changes. RED and GREEN commit fine but refactoring exhausts the budget.

**Why:** Agent context + tool calls accumulate during RED/GREEN, leaving little budget for refactor. Complex fixture design (e.g., Louvain community detection) can consume the entire budget before any commits.

**How to apply:** When launching execution agents: (1) provide pre-written implementation code if available from a failed prior attempt, (2) keep scope to one concern per agent, (3) tell agents to commit early and often — refactor can be a separate commit that's easy to finish manually.
