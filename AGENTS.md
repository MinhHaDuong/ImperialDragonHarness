# Harness agent profiles

Choose agents and concrete models on the fly using the active runtime's available
capabilities. The harness describes the profiles it needs; it does not prescribe
model names, fixed agent definitions, or a runtime-specific implementation.

| Requested profile | Capability class | Effort | Typical responsibility |
|---|---|---|---|
| Cheaper worker | cheap | economy | Search, extraction, mechanical checks, bounded execution |
| Competent worker | standard | standard | Planning, orchestration, ordinary review |
| Expert worker | strong | standard | Difficult implementation or cross-cutting judgment |
| Smartest advisor | frontier | intensive when needed | Hard decisions, adversarial judgment, escalation |

Use the least expensive profile adequate for the task. Promote capability when
the task requires it; organizational rank alone does not determine difficulty.
Reserve intensive effort for tasks that benefit from it rather than broad fan-out.

Skills state intentions with `model-level: auto|cheap|standard|strong|frontier`
and `effort: economy|standard|intensive`. These are relative capability and effort
classes, not model IDs or native launch parameters. Apply each child's declared
intentions independently; let the runtime choose how to realize them. `auto`
delegates the choice explicitly to the runtime. When independent verification is
requested, choose a reviewer decorrelated from the producer when available and
report any limitation.

External reviewer discovery and routing also belong to the active runtime.
Request independent reviewers with the required expertise, capability class,
and access to the review material; let the runtime find who is available and
route between llama.cpp on Padmé, OpenRouter, other local agents, or agents on
another host. These are possible resources, not a mandatory roster or preference
order. Use existing helpers when useful; do not require one gateway or transport.
Record the reviewer identity, route, evidence, and any unavailable perspective.

Project instructions and ticket conventions: [CLAUDE.md](CLAUDE.md).
