# Portable model capability and effort policy

**Status:** design note / migration proposal  
**Date:** 2026-09-24

## Decision

IDH should stop treating vendor model names as architectural roles. Portable
skills and agent profiles should declare semantic requirements; runtime adapters
should resolve them to concrete models and provider-specific controls.

Keep four independent axes:

1. **capability** — minimum competence required;
2. **effort** — requested deliberation;
3. **backend** — allowed/preferred execution pool;
4. **traits** — coding, tools, privacy, context, structured output,
   decorrelation, etc.

Cost is a resolver objective, not a capability level.

Default organizational policy:

```text
MOE/interface       L3 / standard
  └─ team lead      L2 / economy
       └─ executor  L1 / economy
```

This is a default, not a caste system. A difficult coding executor may request
L3; a mechanical worker may request L0. Organizational depth and cognitive
difficulty are separate.

Principle:

> Use the lowest capability adequate for the responsibility, at the lowest
> effort adequate for the uncertainty. Escalate capability before extreme
> effort.

## Audit of current IDH

### What is already right

The three-level topology is explicit. `rules/workflow.md` places the interface
session at MOE N+2, governing by intention through team leads.
`agents/team-lead.md` receives intent, decomposes it, mobilizes executor
subagents, verifies them and synthesizes one report. `rules/claude-code.md`
requires nesting depth >=2 so delegation does not silently flatten.

The harness also correctly learned that model and effort propagation are
runtime-specific. Ticket 0235 and
`memory/feedback_subagent_model_effort_levers.md` distinguish per-launch model
pins from effort controls on definitions/Workflow calls/forks. Preserve that
knowledge.

### What is not portable

The rightsizing API is still Claude-shaped:

- `rules/claude-code.md` requires fan-out launches to pin
  `sonnet|opus|haiku|fable`;
- `tests/test_model_rightsizing.py` makes those names the valid vocabulary;
- `skills/raid/SKILL.md` assigns Sonnet to planning/review, Haiku to
  mechanical checks, and Opus to mutating coders;
- `skills/hunt/SKILL.md` pins its coding executor to Opus;
- `scripts/trace-stats.py` resolves pricing by Claude family name.

Those concrete choices fixed runaway inheritance, but they belong in a Claude
adapter rather than the portable orchestration contract.

### Middle-layer over-allocation is currently possible

`agents/team-lead.md` has neither model nor effort frontmatter. Under the
documented Claude semantics it therefore inherits the session. An Opus/medium
MOE can create an Opus/medium lead even though the lead owns a bounded intent.
The hierarchy should make this allocation explicit.

### Effort is not a portable enum

IDH already has contrary provider semantics. The OpenRouter project memory
records that omitting `reasoning_effort` produced no reasoning while
`minimal` turned reasoning on. Padmé uses `llama-server`/llama.cpp, not
Ollama, and its local models expose another reasoning surface. The 2026-09-23
Padmé reviewer trial also observed `reasoning_content` and provider-specific
suppression.

Therefore Claude's `low|medium|high|xhigh|max` must not become IDH's portable
contract.

## Semantic API

### Capability

Use five ordered requirements:

```text
L0 mechanical   extraction, grep-like classification, formatting
L1 routine      bounded execution with clear instructions and cheap verification
L2 capable      decomposition or judgment within a bounded domain
L3 strong       global orchestration, difficult coding/reasoning, ambiguous synthesis
L4 frontier     exceptional hard-tail work
```

These are engineering contracts, not benchmark scores. A model registry says
which levels a concrete model is eligible to serve.

### Effort

Expose only:

```text
economy
standard
intensive
```

Adapters translate these to legal provider controls. Also support an explicit
`reasoning: off` requirement where a provider distinguishes no reasoning from
minimum reasoning. Do not encode xhigh/max in portable skills.

### Backend

Backend is orthogonal to capability:

```yaml
backend:
  allow: [local, openrouter, anthropic]
  prefer: local
```

Padmé is not a low-tier backend. It is an execution pool whose loaded models
have individual capability qualifications.

### Traits

Traits capture non-ordinal requirements:

```yaml
traits: [coding, repository-mutation, structured-output, long-context]
decorrelate_from: producer
```

Reviewer decorrelation should mean "different family/provider from producer
where practical", not "Sonnet reviews Opus."

## Resolver

A portable launch request should look approximately like:

```yaml
role: executor
capability: L2
effort: economy
traits: [coding, repository-mutation]
backend:
  allow: [anthropic, openrouter, local]
```

A registry owns concrete candidates:

```yaml
models:
  anthropic/<model>:
    backend: anthropic
    capability: L3
    effort_adapter: claude
  openrouter/<model>:
    backend: openrouter
    capability: L2
    effort_adapter: openrouter
  padme/<gguf-model>:
    backend: local
    runtime: llama.cpp
    capability: L1
    effort_adapter: llama-cpp
```

The names above are placeholders deliberately: current product names belong in
live configuration, not this design.

Resolution chooses the cheapest eligible candidate subject to minimum
capability, backend, tools/context/output requirements and decorrelation.
It should return an auditable explanation:

```text
requested: L2/economy + coding
resolved:  openrouter/<model>
reason:    cheapest eligible candidate; local pool lacks coding-L2 qualification
```

No calibrated success probability is required. Capability qualification is an
engineering judgment; measurements may refine it later.

## Role defaults and promotion

| Role | Capability | Effort |
|---|---|---|
| MOE/interface | L3 | standard |
| team lead | L2 | economy |
| executor | L1 | economy |
| mechanical helper | L0 | economy/off |
| hard-tail escalation | L4 | intensive |

Promote by task, not rank:

- difficult repository mutation -> L3/standard;
- cross-cutting design/review -> L2-L3/standard;
- extraction/search -> L0-L1/economy;
- repeated failure -> capability promotion before intensive effort.

## Portability boundary

Portable rules/skills contain capability, semantic effort, traits, backend
constraints/preferences and decorrelation requirements.

Adapters contain concrete model IDs, provider effort syntax, inheritance quirks,
launch schemas, availability and conversion to legal invocations.

Thus `rules/claude-code.md` remains valuable, but as adapter knowledge rather
than IDH's model ontology.

## Migration path

### Phase 0 — representation only

Add semantic vocabulary and registry schema. Populate mappings so every current
pin resolves to exactly its present concrete model. Resolver dry-runs must
reproduce current launch configurations. No behavior change.

This separation matters because the previous trace A/B exercise was invalidated
by simultaneous regime drift.

### Phase 1 — semantic aliases beside concrete pins

Let launch sites request a semantic profile while retaining the old concrete
pin as assertion/fallback. Tests require semantic resolution and legacy pins to
agree. Still no model-mix change.

### Phase 2 — agent profiles, starting with team-lead

Make `team-lead` the first semantic profile: L2/economy. Initially the adapter
may map it conservatively, but inheritance must become explicit rather than
accidental. Then migrate dedicated review profiles.

### Phase 3 — high-fan-out skills

Migrate `raid`, `gaze`, `review-pr`, `review-pr-prose`,
`verify-gate`, audits and release checks by behavioral class:

1. mechanical checks;
2. routine reviewers/researchers;
3. bounded planners/leads;
4. mutating coders;
5. skeptics/judges;
6. exceptional diagnosis.

Do not search-and-replace model names.

### Phase 4 — provider adapters

Implement independently:

- Claude Code: short model tokens plus effort on the correct surface;
- OpenRouter: registry choice and explicit distinction between omitted
  reasoning and minimal/low reasoning;
- llama.cpp/Padmé: currently available local model plus only explicitly
  qualified capabilities;
- Codex/Pi: their own model/effort controls.

Missing mappings fail loudly or use an explicit fallback. Never silently inherit
the caller's expensive configuration.

### Phase 5 — backend choice

Only after semantic migration should the resolver choose among providers.
Start with low-risk classes: mechanical work, extraction and constrained
structured review. Keep difficult mutations explicitly high-capability until
alternative registry entries are qualified.

### Phase 6 — economic policy

Finally change defaults centrally to L3/standard -> L2/economy -> L1/economy,
with task promotion and escalation. This realizes fan-out savings without
mixing architecture migration with an economic experiment.

## Tests and invariants

Evolve `tests/test_model_rightsizing.py` toward these invariants:

1. every fan-out declares an explicit semantic requirement;
2. portable skills do not name concrete model families;
3. every request resolves or fails loudly;
4. unresolved requests never inherit caller model/effort silently;
5. requested reviewer decorrelation is enforced;
6. L0/L1 fan-out cannot resolve to L4 absent explicit fallback;
7. intensive/max-like effort is not a broad fan-out default;
8. "reasoning off" is tested separately from "minimum reasoning";
9. local/cheap does not imply low or high capability;
10. traces record requested profile, resolved backend/model and effective effort.

Keep adapter-level tests for Claude's legal model tokens and other runtime
mechanics; they no longer belong in portable policy tests.

## Non-goals / traps

- Do not rename Sonnet=L1, Opus=L3, etc.; levels are requirements, not aliases.
- Do not infer capability from price, parameter count or provider.
- Do not make organizational rank determine executor capability.
- Do not equate "reasoning off" with lowest effort without adapter evidence.
- Do not calibrate levels from unreliable historical traces.
- Do not use a global cap that overrides deliberate high-capability tasks.
- Do not require a benchmark campaign before adopting the abstraction.

## Open decisions

1. Canonical authoring vocabulary: terse L0..L4, or human labels with L-levels
   only as internal representation?
2. Unavailable minimum capability: default recommendation is promote upward
   when budget permits; downgrade only by explicit opt-in.
3. Registry ownership: recommended one semantic schema with adapter-owned
   concrete entries.
4. Qualification provenance: record why a model is admitted at a level, without
   demanding statistically meaningful benchmarking.
5. Dynamic local availability: Padmé must distinguish registered models from
   currently loaded/available models.
6. Tool competence remains a hard eligibility constraint, not part of the
   ordinal capability score.

## Recommended first implementation slice

Implement only the semantic types, registry schema, resolver dry-run and tests
that reproduce today's routing. Do **not** change live model selection in the
same PR.

That gives IDH the durable abstraction first. Team-lead rightsizing and
cross-provider routing then become configuration/policy changes rather than
rewrites of orchestration logic.
