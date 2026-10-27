# Subagent model/effort levers

Scope: how model and effort settings reach spawned subagents in the runtimes
measured below. Scoped reference notes, each measured on one runtime and
version; re-verify on other runtimes before relying on them. The standing
guidance is `rules/claude-code.md` § Subagent levers.

## Supported observations

The source note reports that model and effort propagate by different
mechanisms, and neither propagates from skill frontmatter: the model lever is
a per-invocation pin on each launch, while effort is pinned on the agent
definition (a definition without the field inherits the session's), and the
workflow spawn path additionally accepts a per-call effort option. The note
measured this on 2026-09-10 (Claude Code 2.1.267, one model, session effort
high) with a four-arm table including no-field and max controls, and records
that its own prior version asserted the opposite for one mechanism.

Refresh, 2026-10-08 (ticket 1063, wave A0): in Claude Code an `Agent` launch
whose definition carried `model: standard` or `model: strong`, with no
per-launch model, failed with HTTP 404 `model_not_found`, the token sent to
the API verbatim. A per-launch `model=haiku` overrode the token and ran as
`claude-haiku-5-5`; an unpinned general-purpose launch inherited the session
model. The `model:` tokens were then removed from agent files. This agrees
with the rule. A planning review had suspected those tier pins were never
honoured; the 404 is consistent with that, measured on one version.

Other runtimes, same period: Codex `spawn_agent` honoured `model` and
`reasoning_effort` overrides (child `turn_context` read, 2026-10-09); with
`fork_turns` "all", 46 of 109 calls carried a model override, honouring not
measured. On Codex 0.161.0 a model's own answer to "which model are you" was
wrong; the session header was the reliable read. The ticket 1071 round
recorded that the source note lacks the `fable` token (accepted, not fixed).

## Sources and exceptions

- [Subagent model/effort levers](../feedback_subagent_model_effort_levers.md) — scoped reference note, interpreted, one runtime and version.
- [Routing waves A0 to C](../journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md)
- [Routing review round](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md)
- [Routing review round two](../journal/2026/2026-10-09-routing-review-round-two.md)
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
