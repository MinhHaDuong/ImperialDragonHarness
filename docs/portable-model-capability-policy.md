# Portable model and effort policy

**Status:** design note / migration proposal  
**Date:** 2026-09-24

## Decision

IDH should express **how much model capability and deliberation a task deserves**,
without maintaining its own catalogue of concrete models.

Portable skills and agent profiles use two small semantic controls:

```text
model-level: auto | cheap | standard | strong | frontier
effort:      economy | standard | intensive
```

Runtime adapters translate those intentions into whatever their runtime supports.
Concrete model names, availability, pricing, provider reasoning syntax, and local
model loading remain runtime/configuration concerns.

The boundary is:

> **IDH specifies orchestration intent. The runtime supplies models.**

Portability is deliberately lossy: adapters preserve intent as far as their
runtime permits; they do not pretend that provider controls are semantically
identical.

## Why

IDH is portable across Claude Code, Codex, Pi, OpenRouter and local llama.cpp
execution on Padmé. Rules such as "workers use Sonnet" solve today's cost problem
but make orchestration depend on one vendor's current product ladder.

The opposite extreme is also undesirable. A harness-wide model registry with
capability matrices, lifecycle state, pricing and provider metadata would
duplicate responsibilities better owned by runtimes and model gateways.

IDH needs only enough abstraction to prevent accidental expensive inheritance
and to communicate intentional rightsizing.

## Current-state audit

### The organizational architecture is already right

`rules/workflow.md` places the interface session at MOE N+2, governing by
intention through team leads. `agents/team-lead.md` receives an intent-level
directive, decomposes it, mobilizes executor subagents, verifies results and
returns one synthesis. `rules/claude-code.md` requires nesting depth >=2.

The topology is therefore already:

```text
author/MOA -> MOE -> team lead -> executors
```

### The current rightsizing implementation is Claude-shaped

The existing implementation is technically disciplined but uses concrete Claude
tiers as its portable vocabulary:

- `rules/claude-code.md` requires fan-out launches to pin
  `sonnet|opus|haiku|fable`;
- `tests/test_model_rightsizing.py` validates those names;
- `skills/raid/SKILL.md` assigns Sonnet to planning/review, Haiku to
  mechanical checks and Opus to mutating coders;
- `skills/hunt/SKILL.md` pins its coding executor to Opus;
- `scripts/trace-stats.py` understands Claude pricing families.

Ticket 0235 and `memory/feedback_subagent_model_effort_levers.md` document why
this exists: unpinned fan-out can silently inherit an expensive session model.
That lesson remains valid. The concrete mechanism belongs in the Claude adapter.

### The middle layer can inherit unnecessarily expensive settings

`agents/team-lead.md` currently has neither a model nor effort declaration.
Under the documented Claude Code behavior it inherits the session. An
Opus/medium MOE can therefore create an Opus/medium lead even though the lead
owns a bounded intent.

The new policy should make this choice explicit without hard-coding Opus or any
future replacement.

### Effort semantics differ across runtimes

IDH already has evidence that provider controls are not interchangeable.
OpenRouter project memory records that omitting `reasoning_effort` produced no
reasoning while `minimal` turned reasoning on. Padmé uses
`llama-server`/llama.cpp and has its own reasoning behavior.

Therefore Claude's `low|medium|high|xhigh|max` must not become the portable
IDH vocabulary.

## Portable contract

### Model level

```text
auto       let the runtime choose
cheap      explicitly favor low-cost capability
standard   ordinary competent model
strong     deliberately spend for a difficult task
frontier   best available; exceptional hard-tail work
```

These are **relative intentions**, not capability scores and not aliases for
particular models.

`auto` is important. Modern runtimes increasingly have their own routing and
model-selection logic. IDH should override that only when orchestration knows
something useful about the task.

A worker's organizational rank does not determine its model level. A mechanical
worker can be `cheap`; a difficult concurrency repair can be `strong` even
though it sits at the bottom of the delegation tree.

### Effort

```text
economy     avoid unnecessary deliberation
standard    normal runtime deliberation
intensive   deliberately spend extra deliberation
```

These are intentions. An adapter may map two levels to the same runtime setting
when the runtime cannot express the distinction.

"Reasoning off" is provider-specific and should remain adapter/configuration
behavior rather than a fourth portable effort level.

### Optional constraints

IDH may state constraints that arise from orchestration rather than model
cataloguing, for example:

- local-only / cloud-allowed when privacy or execution location matters;
- reviewer must be decorrelated from producer;
- task requires tools or repository mutation.

These constraints should remain sparse. IDH should not grow a model capability
database to resolve them.

## Default role policy

A useful default is:

| Role | Model level | Effort |
|---|---|---|
| MOE/interface | strong | standard |
| team lead | standard | economy |
| executor | auto | economy |
| mechanical helper | cheap | economy |
| hard-tail escalation | frontier | intensive |

This expresses the fan-out economics without claiming that all workers are easy.

Task-specific promotion is expected:

- difficult repository mutation -> `strong/standard`;
- cross-cutting judgment/review -> `standard` or `strong`;
- extraction/search -> `cheap/economy`;
- repeated failure -> increase model level before using `intensive` effort.

The general rule is:

> Use the least expensive level adequate for the responsibility. Prefer a
> stronger model at moderate effort to extreme effort on a weaker model.

## Harness/runtime frontier

| Concern | IDH | Runtime / adapter |
|---|:---:|:---:|
| MOE -> lead -> worker hierarchy | yes | |
| task deserves cheaper/stronger intelligence | yes | |
| task deserves more deliberation | yes | |
| reviewer should differ from producer | yes | |
| concrete model name | | yes |
| model availability | | yes |
| pricing | | yes |
| lifecycle/deprecation | | yes |
| provider reasoning syntax | | yes |
| model-specific strengths | | yes |
| local GPU/model loading | | yes |

This frontier is intentional. IDH is an orchestration harness, not a model
gateway.

## Runtime mappings

Adapters need only a small mapping/configuration surface. Conceptually:

```text
Claude:
    cheap     -> configured cheap tier
    standard  -> configured standard tier
    strong    -> configured strong tier
    frontier  -> configured frontier tier

OpenRouter:
    cheap     -> configured cheap model
    standard  -> configured default model
    strong    -> configured strong model
    frontier  -> configured frontier model

Padmé / llama.cpp:
    auto      -> current configured local model
    cheap     -> current configured local model
    standard  -> current configured local model, if allowed
    strong/frontier -> unsupported or explicit fallback
```

These are configuration examples, not normative mappings. When model generations
change, the adapter/config changes; portable skills do not.

An unsupported level should either fail clearly or follow an explicitly
configured fallback. It must not silently inherit an expensive caller setting.

## Model churn

Churn is handled by keeping model identity below the portability boundary.

When a provider replaces a model generation, update the runtime mapping. When a
different OpenRouter model becomes the preferred strong model, update OpenRouter
configuration. When the GGUF served on Padmé changes, update the local runtime
configuration.

No `raid`, `hunt`, `team-lead`, or review skill should need editing merely
because model names changed.

IDH does **not** track model lifecycle, benchmark qualification or
task-by-task capability matrices. Those may exist in a runtime or gateway if
useful, but are outside the harness contract.

## Escalation

Escalation operates on the portable controls:

```text
alternative approach
    -> model-level +1
    -> standard effort
    -> intensive effort / frontier
    -> stop / author
```

The sequence is guidance rather than a rigid state machine. A clearly difficult
task may start at `strong`. The invariant is that broad fan-out does not
silently inherit frontier-level compute.

The existing workflow escalation doctrine remains authoritative; this policy
only governs compute allocation within it.

## Migration path

### Phase 0 — define semantics, change no behavior

Add the two semantic controls and adapter mappings that reproduce today's
concrete choices exactly.

Acceptance criterion: a dry-run or test demonstrates that current launch sites
resolve to their existing model/effort behavior.

Do not change economics in this phase. The previous trace A/B work showed how
quickly conclusions become unreliable when several runtime variables drift
together.

### Phase 1 — add semantic aliases beside current pins

Allow launch sites to declare `model-level` and semantic `effort` while the
adapter still checks against the existing concrete pin. Tests require agreement.

This establishes the abstraction without changing live routing.

### Phase 2 — migrate team-lead and dedicated agent profiles

Make `team-lead` the first semantic profile:

```text
model-level: standard
effort: economy
```

Then migrate dedicated review profiles. Accidental inheritance becomes an
explicit choice.

### Phase 3 — migrate high-fan-out skills

Replace concrete model choices in `raid`, `gaze`, review and audit fan-outs
with semantic intentions. Migrate by behavioral class rather than mechanically
renaming model tokens.

The current `tests/test_model_rightsizing.py` should evolve from "every launch
pins a valid Claude name" to "every fan-out either explicitly delegates choice
to `auto` or declares a semantic level, and the active adapter resolves it."

### Phase 4 — thin runtime adapters

Implement only the translation required by each runtime:

- Claude Code: concrete model token plus effort on the correct launch surface;
- OpenRouter: configured model plus its actual reasoning semantics;
- Padmé/llama.cpp: configured local model and supported controls;
- Codex/Pi: their native model/effort controls.

Do not centralize concrete model metadata in IDH.

### Phase 5 — change economic defaults

After migration is behavior-preserving, adopt the default hierarchy:

```text
MOE       strong   / standard
team lead standard / economy
executor  auto     / economy
```

Individual skills promote tasks where their domain knowledge justifies it.

## Tests and invariants

1. Broad fan-out never silently inherits an expensive root configuration.
2. Every launch either declares a semantic level or explicitly says `auto`.
3. Portable skills do not depend on concrete model names.
4. Unsupported semantic levels fail clearly or use an explicit configured
   fallback.
5. Reviewer decorrelation remains enforceable without naming vendor tiers in
   portable policy.
6. `intensive` is not a default for broad fan-out.
7. Adapter tests cover provider-specific model and effort mechanics.
8. Traces record requested semantic level/effort and the concrete result when
   the runtime exposes it.

## Non-goals

- No harness-wide model registry.
- No model capability matrix.
- No benchmark-based automatic ranking.
- No lifecycle/deprecation database.
- No price optimizer in the harness.
- No attempt to make provider effort controls semantically identical.
- No assumption that worker rank implies task difficulty.

## Recommended first implementation slice

Implement the semantic vocabulary and a Claude adapter/mapping that reproduces
today's behavior, plus tests proving that it does.

Do not alter live model selection in the same change.

That is enough to establish the portability boundary. OpenRouter, Padmé,
Codex and Pi mappings can then be added independently without turning IDH into
a model-management system.
