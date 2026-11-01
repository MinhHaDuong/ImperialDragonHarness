<!-- last-reviewed: 2026-11-01 -->
<!-- Module: the floor. Hard limits every agent role obeys, whatever runtime
or profile; nothing in the other rules or in a skill overrides them. Bare
profiles load this file alone, so it states its rules in full.
Loading: rules/README.md § Loading per runtime. -->
# Guards

Every agent role obeys these, in any runtime; no other rule or skill overrides them.

- **Never display credentials.** Never display API keys, tokens, passwords,
  or any credentials in chat text — not even partially, not even in
  "here's what I found" summaries.
- **Write only into the project you were assigned; elsewhere, only tickets.**
  Resolve the project before writing; loading a skill is not authorization to
  write where it lives. To reach the harness or another project, write into
  its `tickets/`: a new ticket or a log line, to report an incident, request a
  change, or report work done to a tracker. An unreachable destination is
  reported, never replaced by another.
- **Past 230K tokens of context, the task is too big: split it.** Stop and
  hand a proposed split to whoever launched you. Never answer a context wall
  with a bigger window, KV tricks or compaction.
