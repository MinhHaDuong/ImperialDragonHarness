---
name: trace-usage-dedupe-by-message-id
description: Session-trace JSONL repeats the same message.usage object on every content-block row — sum per unique message.id or overstate token costs ~2.7x
metadata:
  type: feedback
---

In Claude Code session traces (`~/.claude/projects/<dir>/*.jsonl` and
`subagents/agent-*.jsonl`), one assistant message spans multiple JSONL
rows — one per content block — and **each row repeats the same
`message.usage` object**. Summing usage per row overstates all four
token categories: measured 248 usage rows vs 96 unique `message.id`s in
one main trace (~2.7x inflation). Also present: `<synthetic>` model
records carrying no real API cost.

**Why:** A 2026-06-10 spot analysis of a raid wave claimed ~$234/wave;
skeptical re-measurement with dedupe gave ~$152 all-Opus upper bound
(~$130-140 with the real Opus/Sonnet mix). The wrong number nearly
became the ground-truth test in ticket 0237 — the spot-check criterion
would have required the census script to reproduce the bug.

**How to apply:** Any trace accounting (trace-doctor study, tickets
0236/0237, ad-hoc cost analyses) must count one usage per unique
`message.id`, price each message by its own `model` field (sessions mix
models), and exclude `<synthetic>` records from $. When citing trace
costs, state whether the figure is deduped.
