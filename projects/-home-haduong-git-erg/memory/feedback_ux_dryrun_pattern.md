---
name: ux-dryrun-pattern
description: AI persona dry-run pattern for UX audits — cold-prompt agent with structured output
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab85764b-ab19-4e89-9279-6343d85d20e6
---

Structured output format for UX dry-run agents works well: ask for **Transcript** (numbered steps, literal output), **Friction log** (What / Where / Severity / Suggestion), **Summary** (3–4 sentences). The agent stays honest when told to quote actual output and not skip confusion.

**Why:** Path A and Path B both produced actionable findings in one pass with this format. Unstructured "report what was hard" prompts tend to produce prose summaries that miss specifics.

**How to apply:** When spawning a UX dry-run agent, include the three-section output format verbatim in the prompt. See `UX-PROCESS.md` for the full cold prompts.

Friction finding from 0152: tickets created with `erg new` in the main repo's working tree (not the worktree) are invisible to the worktree's `git add`. Always create ticket files inside the worktree, or `cp` them in before committing.
