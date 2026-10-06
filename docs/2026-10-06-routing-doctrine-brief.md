# LLM routing doctrine in IDH — brief for review

**Status:** synthesis of existing sources plus one author statement of
2026-10-06; not a spec. It adds no rule. Its job is to give four later reviews
one shared, checkable description of the doctrine and of what implements it.

**The spec** for compute allocation is
[portable-model-capability-policy.md](portable-model-capability-policy.md)
(PR #1002, tracker 0974). Two other documents specify adjacent parts:
[reviewer attribution](2026-10-02-reviewer-attribution-design.md) (who reviewed
and how we learn which reviewer is worth routing to) and the
[tournament concept note](2026-10-03-model-tournament-concept.md) (how a routing
verdict is measured; tracker 1024, in flight and not on `main` when this brief
was written). **No single document states the routing doctrine end to end.**
The gaps are listed in § Open and missing.

Provenance labels used below: **settled** (approved, in a source),
**author-stated** (said by the author in session, now written down here for the
first time), **open** (named as undecided in a source), **derived** (my
arithmetic or inference, labelled as such).

## Why

1. **Silent inheritance is the expensive failure.** A spawned agent defaults to
   the session's model. An Opus-class interface session therefore creates
   Opus-class workers and team leads unless each launch says otherwise. Source:
   policy § The middle layer…, ticket 0235, memory
   `feedback_subagent_model_effort_levers`. *Settled.*
2. **Portability.** IDH runs on Claude Code, Codex, Pi, Mistral Vibe,
   OpenRouter and local llama.cpp on Padmé. "Workers use Sonnet" ties the
   orchestration to one vendor's product ladder. *Settled.*
3. **Model churn belongs below the boundary.** Names, availability, pricing and
   deprecation change monthly; skills must not need edits when they do.
   *Settled.*
4. **Review quality needs independence.** A reviewer from the producer's own
   model family adds less than one from another. Decorrelation is cited from
   literature, not yet measured here (attribution design § 1, finding 4).
   *Settled as intent, open as measurement.*
5. **Subscription quota is scarce.** Author direction of 2026-10-05: route more
   aggressively to conserve Claude Pro Max, ChatGPT Pro and Vibe Pro quotas;
   consider the GLM Coding Plan after 1024. *Open: no architecture, provider or
   purchase is selected* (ticket 0974 § Open design point).

## What

**Boundary.** "IDH specifies orchestration intent. The runtime supplies
models." Concrete model names, availability, pricing, provider reasoning syntax
and local model loading are the runtime's. *Settled* (policy § Decision,
§ Harness/runtime frontier).

**Two portable controls.**

```text
model-level: auto | cheap | standard | strong | frontier
effort:      economy | standard | intensive
```

Relative intentions, not capability scores and not model aliases. An adapter may
map two levels to one runtime setting. *Settled.*

**`auto`** means "the runtime's router chooses". Where no router exists it
resolves to a configured default tier, never to the caller's model. *Settled.*

**`decorrelated-from: <producer launch>`** is the one constraint levels cannot
express. The adapter resolves it from what it knows of both concrete models: at
minimum a different family or tier, another vendor where available. *Settled as
a design; no resolver exists* (§ Open and missing).

**Default roles.** MOE/interface strong/standard; team lead standard/standard;
executor auto/economy; mechanical helper cheap/economy; hard-tail escalation
frontier/intensive. The MOE row is a recommendation to the author: the session's
model is chosen at start and IDH cannot pin it. *Settled* (policy § Default role
policy).

**General rule.** Least expensive level adequate for the responsibility; a
stronger model at moderate effort beats a weaker one at extreme effort.
*Settled.*

**Escalation ladder.** alternative approach → model-level +1 → standard effort →
`intensive` / `frontier` → stop and ask the author. Guidance, not a state
machine. *Settled* (policy § Escalation; `rules/workflow.md` § Escalation
protocol stays authoritative).

**Frontier and intensive are one-shot advisor calls.** Author-stated
2026-10-06. Models of the Astra or Fable class, at `intensive` effort, are for
**single calls on a deep, well-defined problem**:

- the ticket that cannot be done and cannot be split;
- a manuscript review on the substance of the scientific argument and methods;
- a design review of a critical feature (in the harness or in erg, many are).

They are never a standing setting of an orchestrator, a team lead or a fan-out
member. The call is one-shot with a self-contained brief. The policy table's
"hard-tail escalation" row already points this way; the three cases and the
one-shot condition were not written anywhere before this brief.

**Not in the doctrine** (policy § Non-goals): a model registry, a capability
matrix, benchmark-based automatic ranking, a lifecycle database, a price
optimizer in the harness, identical semantics across providers' effort
controls, any assumption that rank implies difficulty.

## Where

| Layer | Holds | Source |
|---|---|---|
| Spec | the contract, role defaults, escalation, invariants 1–9 | `docs/portable-model-capability-policy.md` |
| Rules | delegation doctrine; Claude Code lever mechanics | `rules/workflow.md` § Delegation; `rules/claude-code.md` § Subagent levers |
| Skills | intentions in prose (`model-level`, `Requested effort`) | `skills/*/SKILL.md` |
| Agent profiles | per-role model token | `agents/*.md` frontmatter; contracts in `profiles/*/PROFILE.md` |
| Adapters | runtime translation, registration | `adapters/claude-code/`, `adapters/codex/`, `adapters/pi/` (Pi pins `padme/qwen3.8-27b`: concrete, below the boundary, as intended) |
| Vocabulary | the two enums | `scripts/model_policy.py` constants |
| Measurement | tournament, attribution records, trace surveys | tickets 1024, 1004; `scripts/trace-*.py`; `skills/trace-doctor` |
| Runtime config | concrete mappings, models, prices | outside the repository, by design |

**Claude Code is the one runtime with a rules file.** Its idiosyncrasies sit in
`rules/claude-code.md`, which other runtimes skip. That isolation is the
intended architecture. Until 2026-10-06 it also had a harness-side dry-run class
(`ClaudeMapping`); see § Decisions taken with this brief.

## Who

- **Author (MOA):** sets policy, chooses and buys providers and plans, signs
  waivers, decides escalation to "stop and ask".
- **Interface session (MOE, two levels above executors):** filters, verifies,
  surfaces, advises; governs through team leads by intention. Its model is the
  author's choice at session start.
- **Team lead:** decomposes an intent, mobilizes executors, verifies, returns one
  report. Default standard/standard.
- **Executor and mechanical helper:** bounded work at the cheapest adequate
  level.
- **Advisor (frontier, one-shot):** the three cases above.
- **Reviewer:** decorrelated from the producer where available; its identity
  comes from runtime evidence, never from a configured name.
- **Runtime/adapter:** owns concrete model, availability, price, provider
  syntax. 2026-10-01 decision.

## When

- **Session start:** the author picks the interface model. IDH cannot override.
- **Each launch:** the launch declares a level or says `auto`. On Claude Code
  `auto` has no router, so the launch pins a model token explicitly.
- **On repeated failure:** climb the ladder, model level before effort.
- **After a merge:** `/roar` captures review attribution facts; coaching is
  ex post and offline (attribution design § 2).
- **When a provider changes models:** the runtime mapping changes, no skill
  does.
- **Phase 5 and the tournament verdict:** economic defaults, including whether
  team leads may drop to `economy`, are decided on measured verification quality
  after 1024. *Open.*

## How

**Declaration.** Skills state intent in prose (`model-level: …`,
`Requested effort: …`). Semantic effort stays in prose because native
frontmatter parsers may read `effort` as a provider enum (policy § Implemented
skill boundary).

**Claude Code mechanics** (memory `feedback_subagent_model_effort_levers`,
measured 2026-09-10 on Claude Code 2.1.267, Opus 5, session effort `high`):

- a skill's `model:` never reaches the agents it spawns; `Agent` and
  `Workflow.agent()` default to the session model unless a per-call `model` is
  passed (short enum token; a full id is valid only in frontmatter);
- `Agent` has no `effort` parameter; effort is pinned by the agent definition's
  `effort:` field; `Workflow.agent()` accepts `opts.effort` per call;
- on models with a pinned default effort the frontmatter key was unreliable
  before 2.1.267 (not tested here).

**Learning which reviewer to route to.** Runtimes review their own way. The
harness's contract is a record format. Roar writes one attribution record per
reviewed merge; ranking, correlation and marginal coverage are derived at read
time. Statistics are pre-registered: Beta-Binomial, Jeffreys prior, 90% credible
intervals; eliminate a seat at ≥10 labeled games when the upper bound of its
false-finding share exceeds 0.5; promote only on non-overlapping intervals;
estimates valid per recorded model version (attribution design § 7).

**Learning which stack to route to.** Paired, blind, full-crossover comparison
on harness work; verdicts are stack-level (model × engine), time-stamped, single
machine (tournament concept §§ 3, 6). The first instance decides Padmé's local
seats and doubles as a local-versus-hosted value comparison.

**Quota-aware routing** (*open*): two candidate routes were named, an LLM-routing
MCP plugin usable from Claude and Codex, or tuning evidence-based IDH routing.
Fact verified 2026-10-05: GLM Coding Plan off-peak consumes half of standard
usage credits, not half the subscription price; promotion all day through
2026-10-07. Source cited in the ticket: docs.z.ai/devpack/overview.

## How much

No cost figure in this doctrine is a measurement unless a source says so.
Trace-doctor reports are list-price API-equivalent "shadow dollars" under
subscription auth: capacity consumption, never invoiced money. Anything divided
out of those is *derived* and must say so. Local-model costs are hardware and
time, not dollars; the tournament records latency separately.

## Decisions taken with this brief (2026-10-06)

- **Invariant 6:** resolved by the one-shot doctrine above. `skills/raid`
  carried `Requested effort: intensive` for the orchestrator; it is now
  `standard`. No test: a test scanning prose is brittle and the repository
  prefers removing guards to growing them.
- **Invariants 4, 7, 9:** waived in writing (author choice "C"). The harness
  holds no live translation code; `ClaudeMapping` had no caller outside its own
  tests and is removed. Invariants 4 and 9 remain true only as rule text
  (`rules/claude-code.md`: pin a model on every fan-out launch) plus the
  text-level test `test_fanout_skill_bodies_declare_model_level`. **Residual
  risk:** nothing executable states "`auto` never resolves to the caller's
  model" any more.
- **Invariant 8:** attached to Phase 5, which needs traces and waits for 1024.
  Attribution records already carry the writer's `model` and `effort` (the
  concrete result); the requested level is recorded nowhere.
- **Invariant 1:** partial. A text-level test checks that a fan-out skill body
  declares a level; no test observes a launch.

## Open and missing

1. No single spec states the routing doctrine; this brief is a stopgap.
2. **Decorrelation has no resolver and no test** (invariant 5). `decorrelated-from`
   is declared in `skills/biblio-saturation` only; other skills and
   `rules/workflow.md` say it in prose.
3. **Quota-aware routing** has no design, only a question (ticket 0974).
4. **`auto` on Claude Code** has no live implementation; it is a rule.
5. **Traces do not record the requested level.** Where a runtime masks the model
   (Mistral Vibe), even the concrete result is unavailable; the runtime-masked
   identity type landed with PR #1220 (ticket 1038) so that the gap is recorded
   honestly instead of reconstructed.
6. **Phase 2 and Phase 5 are unfiled.** `agents/team-lead.md` declares neither
   model nor effort.
7. **No per-runtime statement of model/effort support** exists in
   `adapters/pilot-support.json`, the inventory that already tracks per-harness
   assertions with an evidence kind. Whether Codex and Pi expose model and effort
   controls was not read for this brief.

## Testable assumptions of the doctrine

Each can fail independently; the reviews below should check them one by one.

| # | Assumption | Held how |
|---|---|---|
| A1 | Subagent launches inherit the session model unless pinned (Claude Code) | measured 2026-09-10, one version, one model |
| A2 | Effort controls are not portable across providers | OpenRouter: omitting `reasoning_effort` gave no reasoning while `minimal` enabled it (project memory); not re-measured |
| A3 | Concrete model names churn faster than orchestration doctrine | asserted |
| A4 | A different family or vendor reviews with lower correlation than the same family | cited from literature, not measured here |
| A5 | Stronger model at moderate effort beats weaker model at extreme effort | asserted in the spec; the tournament varies effort inside arms |
| A6 | Runtimes will keep or grow their own routers, so IDH should override `auto` only with task knowledge | stated as a trajectory ("modern runtimes increasingly…"), no source cited |
| A7 | A one-shot frontier call on a deep, well-defined problem pays for itself against standing high effort | author-stated; no measurement |
| A8 | Quota, not price, is the binding constraint on subscription plans | author-stated 2026-10-05; plan terms change |

## Review brief

Four reviews, each independent, each told to report with the repository's
diagnosis discipline: observation first, cause held until isolated, a null
result not counted until a positive control fired.

**R1 — doctrine versus the state of the art.** Questions: how do published and
production systems route between models (cascades, learned routers, cost-aware
selection, mixture patterns), and which of A4, A5, A7 does the literature
support, contradict or leave untested. Output: per assumption, evidence for and
against with citations; a list of routing ideas the doctrine ignores. No
recommendation to build a registry or price optimizer without stating the
non-goal it breaks.

**R2 — doctrine versus provider and runtime trajectories.** Questions: for
Claude Code, Codex, Pi, Mistral Vibe, OpenRouter, llama.cpp, what do current
documentation and release notes say about built-in routing, subagent model
selection, effort controls, quota plans and model deprecation; which of A1, A2,
A3, A6, A8 does each confirm or break; what changes within a year. Output:
per runtime, a table of the assumptions it supports, and the dated sources.
Facts older than three months are flagged stale.

**R3 — implementation versus doctrine.** Start from the known gaps in
§ Open and missing and verify, do not trust, these checks:

- do `agents/*.md` frontmatter tokens (`model: standard`, `model: strong`)
  mean anything to Claude Code, or fall through to inheritance? (enum is
  documented elsewhere as short tokens; unverified here, the cheapest probe on
  the list);
- which agent profiles set `effort:` (none found by grep on 2026-10-06);
- where `auto` resolves on each runtime in practice;
- does any skill still carry `intensive` or `frontier` outside the three
  one-shot cases;
- invariant coverage table in ticket 0974.

**R4 — implementation versus ten historical sessions.** Pre-register before
reading: the ten sessions, the questions and the pass criteria are fixed first,
as the attribution design fixes its statistics first.

- *Sample:* ten sessions across at least three runtimes and at least four
  projects (this harness, climate-finance-het, chemin-de-voix, a manuscript
  repository, erg or equivalent), covering executor, team-lead, reviewer and
  advisor roles. State the selection rule; random draws within strata, not
  hand picking. Stratify so Vibe, whose model is masked, is present.
- *Evidence channel:* on Claude Code, each child records its own effort in
  `~/.claude/projects/<proj>/<session-id>/subagents/agent-<id>.jsonl` with the
  sibling `.meta.json` naming `agentType`. Channels for Codex, Pi and Vibe are
  not established; establishing them is part of the work, and a session whose
  model cannot be read is a recorded unknown, not excluded.
- *Per session:* what was declared; what actually ran (model, effort);
  whether an expensive setting was inherited rather than chosen; whether any
  `frontier` or `intensive` use fits the one-shot condition; whether a reviewer
  was decorrelated from its producer, with the basis; the resulting cost, labelled
  measured or derived.
- *Confidentiality:* extracts may hold uncleared material. Per-session
  content is not committed; only aggregates and anchors go into the repository,
  the same boundary `skills/trace-doctor` keeps. Anything uncleared enters as age
  ciphertext through the project's capture mechanism.
- *Output:* a table, one row per session, the unknowns counted, and no
  conclusion drawn from ten sessions beyond "present / absent in this sample".

**Reviewer independence.** Request reviewers decorrelated from the Claude
family that wrote this brief where the runtime offers one, record the actual
identity and route from runtime evidence, and name any unavailable perspective.
