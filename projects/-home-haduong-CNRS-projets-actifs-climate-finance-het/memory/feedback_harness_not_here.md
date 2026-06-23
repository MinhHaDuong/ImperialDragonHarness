---
name: Harness consolidation plan
description: User-level harness moving to ~/.agent/ (from ~/CNRS/code/agentic-harness). Project-level agent config consolidates in <project>/.agent/. Progressively separate user vs project.
type: project
---

Harness architecture (as of 2026-03-25):
- **User-level**: `~/.agent/` (moving from `~/CNRS/code/agentic-harness`)
- **Project-level**: `<project>/.agent/` (consolidating from scattered AGENTS.md, runbooks/, docs/*-guidelines.md, hooks/)

Plan: (1) move agentic-harness → ~/.agent/, (2) consolidate project agent infra into .agent/, (3) progressively separate user vs project content.

Offline tickets (PR #385 / branch t237-local-ticket-system) is dogfooding on its own branch.

**Why:** User wants clean separation between reusable agent framework and project-specific config.
**How to apply:** Harness work now happens both here (project .agent/) and in ~/.agent/ (user-level). Don't mix project-specific content into user-level.
