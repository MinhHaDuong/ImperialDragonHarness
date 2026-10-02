# Subagent model/effort levers

Scope: how model and effort settings reach spawned subagents in the runtime
measured below. A scoped reference note measured on one runtime and version,
not a factual capture; re-verify on other runtimes before relying on it.

## Supported observations

The source note reports that model and effort propagate by different
mechanisms, and neither propagates from skill frontmatter: the model lever is
a per-invocation pin on each launch, while effort is pinned on the agent
definition (a definition without the field inherits the session's), and the
workflow spawn path additionally accepts a per-call effort option. The note
measured this on 2026-09-10 (Claude Code 2.1.267, one model, session effort
high) with a four-arm table including no-field and max controls, and records
that its own prior version asserted the opposite for one mechanism.

## Sources and exceptions

- [Subagent model/effort levers](../feedback_subagent_model_effort_levers.md) — scoped reference note, interpreted, one runtime and version.
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
