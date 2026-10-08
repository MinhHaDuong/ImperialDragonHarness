# LLM routing doctrine in IDH: brief for review

**Status:** superseded in part on 2026-10-08 by tracker 1052 and `skills/route/SKILL.md`: the qualifier spec (`model-level`, `effort`, `auto`, `decorrelated-from`), the default roles and the vocabulary layer below are retired; the decorrelation and measurement material still holds. Consolidated 2026-10-06 from existing sources and the author's
statements of the same day. This note is meant to unify the routing doctrine and
to replace the scattered statements of it. Until the routing skill exists (§ The
routing skill), the sources below keep their specifics: the policy doc keeps the
contract and invariants, the attribution design keeps the record format, the
tournament note keeps the measurement rules. Its first job is to give five
reviews (§ Review questions) one shared, checkable description of the doctrine
and of what implements it.

Sources:
[portable-model-capability-policy.md](portable-model-capability-policy.md)
(PR #1002, tracker 0974), [reviewer attribution
design](2026-10-02-reviewer-attribution-design.md) (who reviewed, and how we
learn which reviewer is worth routing to), [tournament concept
note](2026-10-03-model-tournament-concept.md) (how a routing verdict is
measured; tracker 1024, in flight and not on `main` when this was written),
[agent profile subsystem design](2026-10-03-agent-profile-subsystem-design.md).

Provenance labels: **settled** (approved, in a source), **author-stated** (said
by the author in session, written down here for the first time), **open** (named
as undecided), **derived** (my inference or arithmetic, labelled as such).

## Why

1. **Silent inheritance is the expensive failure.** A spawned agent defaults to
   the session's model. An Opus-class interface session creates Opus-class
   workers and team leads unless each launch says otherwise (policy § The middle
   layer, ticket 0235, memory `feedback_subagent_model_effort_levers`).
   *Settled.*
2. **Portability.** "Workers use Sonnet" ties the orchestration to one vendor's
   product ladder. *Settled.*
3. **Models change; skills should not have to.** When a provider renames or
   retires a model, or its price or availability changes, we edit the runtime
   mapping. No skill or rule is touched. *Settled.*
4. **Review quality needs independence.** A reviewer from the producer's own
   model family adds less than one from another. Decorrelation is cited from
   literature, not measured here (attribution design § 1, finding 4). *Settled as
   intent, open as measurement.*
5. **Quality, cost and speed trade against each other, and the trade moves with
   the clock.** Local models are slow, use electricity and serve one request at
   a time; hosted plans have peak and off-peak windows; subscription quotas run
   out. See § Quality, cost, speed and time. *Author-stated.*
6. **Subscription quota is scarce.** Author direction of 2026-10-05: route more
   aggressively to conserve Claude Pro Max, ChatGPT Pro and Vibe Pro quotas;
   consider the GLM Coding Plan after 1024. *Open: no architecture, provider or
   purchase is selected* (ticket 0974 § Open design point).

## Boundary

"IDH specifies orchestration intent. The runtime supplies models." Concrete model
names, availability, pricing, provider reasoning syntax and local model loading
are the runtime's. *Settled* (policy § Decision, § Harness/runtime frontier).

**Routing is an AI task.** Judging how hard a task is does not mechanize well:
difficulty depends on content, not on keywords or size. In IDH the judge is the
orchestrator, because it is already running and it knows the task.
*Author-stated.* Two alternatives were weighed:

- Ask another model tier to do the routing. Possible, but routing then becomes a
  separate unit of work with its own prompt, cost and failure modes, and the
  question returns: who judges the router? It is potentially recursive.
- Use an external LLM router, such as a gateway or an MCP plugin usable from
  Claude and Codex. Ticket 0974 names it as an alternative. It was not tried and
  there is no verdict.

What IDH keeps: the judgment stays with the orchestrator. Everything mechanical
(route state, cost, grid lookup) moves into a script it consults (§ The routing
skill).

Concrete names, prices and schedules stay below the boundary. A grid that holds
them is a change to the policy's non-goals; see § Direction stated, not decided.

## What

**Superseded 2026-10-08.** The two portable controls, `auto`, `decorrelated-from`, the default-role table, the general rule and the escalation ladder that stood here (all marked *Settled*) were retired by tracker 1052: skills state a role and a need, and `skills/route/SKILL.md` decides the worker. Reviewer independence is a family question (`skills/route/references/decorrelation.md`).

**Two separate rules, not one.** Author-stated 2026-10-06. Class and effort are
orthogonal choices: the class buys depth of judgment, the effort buys thinking
duration.

*The `frontier` class is reserved for one-shot calls on a deep, well-defined
problem* (models of the Astra or Fable class):

- the ticket that cannot be done and cannot be split;
- a manuscript review on the substance of the scientific argument and methods;
- a design review of a critical feature (in the harness or in erg, many are).

It is never the standing setting of an orchestrator, a team lead or a fan-out
member. The call is one-shot with a self-contained brief.

*`intensive` effort is rarely paired with `frontier`.* The pairing makes costs run
away for marginal judgment. `intensive` is not a frontier property: it is the
default strategy of the Qwen 3.8 family, which compensates its size with
duration (template-default XHIGH thinking). The author reports this as measured
in the arena: more steps and tokens at the same effort label. This brief did not
see that data; the source here is the author's note in `AGENTS.md`, and the data
belongs to ticket 1024.

**Not in the doctrine today** (policy § Non-goals): a model registry, a
capability matrix, benchmark-based automatic ranking, a lifecycle database, a
price optimizer in the harness, identical semantics across providers' effort
controls, any assumption that rank implies difficulty.

## Portability

IDH runs under three independent conditions. A given intention resolves
differently in each combination.

| Axis | Values named by the author |
|---|---|
| Interface (runtime) | the TUIs of Claude Code, Codex, Pi, Mistral Vibe, others |
| Route to the model | a vendor's built-in access under a plan; the vendor's direct API; OpenRouter; local llama.cpp; local Strata; others |
| Environment | multi-GPU workstation; laptop on the same VPN; laptop disconnected; web container; CI in a GitHub container; local CI container; others |

A disconnected laptop reaches only local models. A CI container probably has no
GPU and no plan credentials. Evidence is uneven: `adapters/pilot-support.json`
tracks claude, codex and pi, not Vibe; for Strata, the web container and the CI
environments the only sources are tickets. Those cells are **not established**
and this brief leaves them empty rather than fill them.

The policy already says an unsupported level must fail clearly or follow a
configured fallback. It says nothing about a route or an environment that is
unreachable. That gap is review question Q0.

## Quality, cost, speed and time

Routing weighs quality, cost and speed. Everything in this section is
*author-stated* and unmeasured here unless a source is cited.

- **Padmé** (local): slow, uses electricity, serves one model at a time. This
  matches `--parallel 1` for arms A and C in the tournament note. A local fan-out
  is serialized.
- **Electricity**: cheap in the afternoon (solar power); off-peak from midnight
  to 7 am. No tariff is in the repository.
- **Z.ai GLM Coding Plan**: peak is 14:00 to 18:00 (UTC+8), Monday to Friday,
  which is 08:00 to 12:00 in Paris during summer time and 07:00 to 11:00 in winter.
  Outside it, off-peak usage costs half the standard credits (not half the
  subscription price). A promotion makes all hours off-peak through 2026-10-07.
  *Verified 2026-10-05* in the notes of tickets 0980 and 1004; source cited there:
  docs.z.ai/devpack/overview. The peak is that four-hour window, not the whole
  Chinese working day.
- **Quota windows** depend on the plan: a 5-hour block, a week, or a month. A
  route that hit its limit is blocked until reset. The router must not send work
  into a blocked route. A 5-hour quota is spent before its reset; a monthly quota
  is rationed. Plan terms are not verified here.
- **Availability is not liveness.** In the tournament (ticket 1024, note of
  2026-10-06) the OpenAI account had no credits left and Pi logged "You have no
  credits remaining", while the `/v1/models` probe still answered. A blocked seat
  must also never read as a clean review: the attribution design (§ 1, finding 2)
  records quota-blocked seats once graded `ok`, and the record format has
  `status: ran|failed|skipped` for this.
- **Fallback order matters.** If a cheap route is blocked, falling back to a
  scarce subscription burns the quota we are trying to spare. The fallback chain
  is chosen, never inherited. This is a question, not a rule.
- **Urgency is not expressible today.** Neither control says whether a human is
  waiting or the work can run overnight on the local model or off-peak on a
  hosted plan. The orchestrator knows. A candidate third signal, noted as a
  question and not a proposal.

## Where

| Layer | Holds | Source |
|---|---|---|
| Spec | the contract, role defaults, escalation, invariants 1 to 9 | `docs/portable-model-capability-policy.md` |
| Rules | delegation doctrine; Claude Code lever mechanics | `rules/workflow.md` § Delegation; `rules/claude-code.md` § Subagent levers |
| Skills | a role and a need in prose; no qualifiers (retired 2026-10-08) | `skills/*/SKILL.md` |
| Agent profiles | per-role shell and contract | `agents/*.md`; `profiles/*/PROFILE.md` |
| Adapters | runtime translation, registration | `adapters/claude-code/`, `adapters/codex/`, `adapters/pi/` (Pi pins `padme/qwen3.8-27b`: concrete, below the boundary, as intended) |
| Vocabulary | retired 2026-10-08 (was `scripts/model_policy.py`) | none |
| Measurement | tournament, attribution records, trace surveys | tickets 1024, 1004; `scripts/trace-*.py`; `skills/trace-doctor` |
| Routing skill (direction) | performance grid, cached route state, scripts | not built; § The routing skill |
| Runtime config | concrete mappings, models, prices | outside the repository, by design, until the grid exists |

Claude Code is the one runtime with a rules file. Its idiosyncrasies sit in
`rules/claude-code.md`, which other runtimes skip. That isolation is the intended
architecture.

## Profiles and default roles

**How profiles work** (design note 0938, `tests/test_agent_profiles.py`).

- A **shell** is `agents/<name>.md`: frontmatter with `name`, `description`,
  `model` (a short token) and optionally `tools`; a body that is one pointer, "read
  your contract at `profiles/<name>/PROFILE.md`".
- A **contract** is `profiles/<name>/PROFILE.md`: `Rules` to read, `Skills` it may
  invoke, `Charter`. It carries no model; frontmatter is the one source of launch
  parameters, and a test enforces it.
- Nothing validates the pointer at runtime: a convention backed by doc-pin tests.
  If the agent cannot find its contract it says so and stops.
- Five roles have a contract: `coder`, `code-reviewer`, `prose-reviewer`,
  `gate-seat`, `adherence-seat`. Two shells have none: `team-lead` and
  `gaze-pr-review`.

**Relation to the default roles.** A profile is a behavior; a default role is a
compute level tied to a place in the delegation tree. Contracts are orthogonal to
compute. The shell's `model` field is not: it carries the same information as the
role table, in a second place, and on Claude Code it is the only place a per-role
effort can be pinned (effort is set per agent definition, not per call).

Findings, verified by reading on 2026-10-06:

- the table gives the executor `auto/economy`; the only executor profile, `coder`,
  is `strong`; the four seats are `standard` but the table has no reviewer row;
  mechanical helper, advisor and interface have no profile;
- no shell sets `effort`; one role at two efforts would need two profiles;
- skills use `model-level`, shells use `model: standard` in the native field. (superseded 2026-10-08: no qualifiers remain)
  Whether Claude Code understands `model: standard` or falls back to inheritance
  is **not verified**; it is the cheapest probe in the review list;
- the `agents` census channel is 761 of 800 characters; `team-lead`'s description
  alone is 350. A new profile does not fit without shortening it.

**Position.** Do not route every launch through a profile: the 800-character cap
forbids it, the per-launch cost (shell, contract and rules, no cache) would fall on
the cheap fan-outs, and the design deliberately keeps the roster hand-sized.
Consolidate the vocabulary instead: a precedence rule (profile frontmatter over
role default over `auto`), a table mapping profile to role to level with a
reviewer row, a real `team-lead` profile (Phase 2, unfiled), and one name for the
field. *Open: recommended, not decided.*

## Who

- **Author (MOA):** sets policy, chooses and buys providers and plans, signs
  waivers, decides when to stop and ask.
- **Interface session (MOE, two levels above executors):** filters, verifies,
  surfaces, advises; governs through team leads by intention. Its model is the
  author's choice at session start.
- **Team lead:** decomposes an intent, mobilizes executors, verifies, returns one
  report. Default standard/standard.
- **Executor and mechanical helper:** bounded work at the cheapest adequate level.
- **Advisor (frontier, one-shot):** the three cases above.
- **Reviewer:** decorrelated from the producer where available; its identity comes
  from runtime evidence, never from a configured name.
- **Runtime and adapter:** own concrete model, availability, price and provider
  syntax (2026-10-01 decision).

## When

- **Session start:** the author picks the interface model. IDH cannot override it.
- **Each launch:** the launch declares a level or says `auto`. On Claude Code `auto`
  has no router, so the launch pins a model token explicitly.
- **The clock:** afternoon solar hours, the 00:00 to 07:00 off-peak window, the
  peak windows of hosted plans and the reset time of each quota change which route
  is right. Today the doctrine has no place for wall-clock time.
- **On repeated failure:** climb the ladder, model level before effort.
- **After a merge:** `/roar` captures review attribution facts; coaching is ex post
  and offline (attribution design § 2).
- **When a provider changes models:** the runtime mapping changes, no skill does.
- **Phase 5 and the tournament verdict:** economic defaults, including whether team
  leads may drop to `economy`, are decided on measured verification quality after
  1024. *Open.*

## How

(Superseded 2026-10-08.) **Declaration.** Skills state intent in prose (`model-level: …`, `Requested
effort: …`). Semantic effort stays in prose because native frontmatter parsers may
read `effort` as a provider enum (policy § Implemented skill boundary).

**Claude Code mechanics** (memory `feedback_subagent_model_effort_levers`, measured
2026-09-10 on Claude Code 2.1.267, Opus 5, session effort `high`):

- a skill's `model:` never reaches the agents it spawns; `Agent` and
  `Workflow.agent()` default to the session model unless a per-call `model` is
  passed (short enum token; a full id is valid only in frontmatter);
- `Agent` has no `effort` parameter; effort is pinned by the agent definition's
  `effort:` field; `Workflow.agent()` accepts `opts.effort` per call;
- on models with a pinned default effort the frontmatter key was unreliable before
  2.1.267 (not tested here).

**Learning which reviewer to route to.** Runtimes review their own way. The
harness's contract is a record format. Roar writes one attribution record per
reviewed merge; ranking, correlation and marginal coverage are derived at read
time. Statistics are pre-registered: Beta-Binomial, Jeffreys prior, 90% credible
intervals; eliminate a seat at 10 or more labeled games when the upper bound of its
false-finding share exceeds 0.5; promote only on non-overlapping intervals;
estimates valid per recorded model version (attribution design § 7).

**Learning which stack to route to.** Paired, blind, full-crossover comparison on
harness work; verdicts are stack-level (model by engine), time-stamped, single
machine (tournament concept §§ 3, 6). The first instance decides Padmé's local
seats and doubles as a local-versus-hosted value comparison. Effort levels are part
of an arm's definition (tournament concept § 8).

**Candidate model of the levers** (author proposal 2026-10-06, *not adopted*).

- Group models into **clusters** of comparable capability. The orchestrator judges
  the task and picks the cluster.
- Inside the cluster a script picks the **variant** from cost, environment, route
  state, clock and quota. No model call is spent on that step.
- A variant is a model plus its effort setting plus its route: **effort is a trait
  of the model's identity**, not a separate choice per task.
- Today's four levels are already clusters of size one per adapter. The change is a
  list and a selector instead of a single mapping.
- It fits a Claude Code constraint: effort is fixed per agent definition, so a
  variant corresponds to a definition.
- Risks: the grid grows with models times efforts; cluster boundaries are
  arbitrary; strengths depend on the task type (the tournament note, § 6, expects
  task-conditional routing when a coder model wins on code only), which suggests
  cluster by task family; `AGENTS.md` says class and effort should not be coupled.
  They can stay orthogonal as intentions and be joint as candidates, but that is the
  author's call; and a grid of this kind touches the non-goals.

## The routing skill

*Direction, author-stated 2026-10-06; nothing is built.* Routing becomes a skill of
its own, so that it is no longer scattered across the rules and skills of the
harness.

- **`route`** is non-interactive: a subroutine the orchestrator reads, not a
  command a user types (frontmatter intent `user-invocable: false`; whether the
  runtime honors that is not checked). It holds the model performance grid, a cache
  of route state, and scripts that probe routes and look the grid up. It adds no
  model call, so routing does not recurse: the orchestrator remains the judge.
- **`arena`** is user-facing. It replays the tournament benchmark when a new model
  ships, so the grid gets a dated entry. It depends on 1024, and each replay is
  bounded by the spend caps pre-registered there.
- **The grid is a data file, not prose.** The skill-text scanner reads only
  `skills/**/*.md`, and `skills/coaching/benchmark-board.yml` is a precedent for a
  data file beside a skill. Entries need a source and a date; the tournament says
  its own verdict is time-stamped, not eternal.
- **The state cache is machine- and environment-specific and is not committed.** A
  disconnected laptop does not see Padmé. It records failures observed in real use
  with their reset horizon, not only liveness probes (§ Quality, cost, speed and
  time).
- **Skill names** follow function, per `rules/authoring-skills.md`; the skill text
  carries no model names.

## How much

No cost figure in this doctrine is a measurement unless a source says so.
Trace-doctor reports are list-price API-equivalent "shadow dollars" under
subscription auth: capacity consumption, never invoiced money. Anything divided out
of those is *derived* and must say so. Local-model costs are hardware, electricity
and time, not dollars; the tournament records latency separately.

## Decisions taken with this brief (2026-10-06)

- **Invariant 6:** resolved by the two rules above: `frontier` is for one-shot calls
  only, and `intensive` is not a default of any orchestration. `skills/raid`
  carried `Requested effort: intensive` for the orchestrator; it is now `standard`,
  and its advisor role is `frontier` at `standard` effort. No test: a test scanning
  prose is brittle and the repository prefers removing guards to growing them.
- **Invariants 4, 7, 9:** waived in writing (author choice "C"). The harness holds
  no live translation code; `ClaudeMapping` had no caller outside its own tests and
  is removed. Invariants 4 and 9 remain true only as rule text
  (`rules/claude-code.md`: pin a model on every fan-out launch) plus the text-level
  test `test_fanout_skill_bodies_declare_model_level`. **Residual risk:** nothing
  executable states "`auto` never resolves to the caller's model" any more.
- **Invariant 8:** attached to Phase 5, which needs traces and waits for 1024.
  Attribution records already carry the writer's `model` and `effort` (the
  concrete result); the requested level is recorded nowhere.
- **Invariant 1:** partial. A text-level test checks that a fan-out skill body
  declares a level; no test observes a launch.

## Direction stated, not decided

1. **Routing as a skill** (`route`, `arena`). Owners and build order are open.
2. **The policy's non-goals** (registry, capability matrix, benchmark ranking,
   lifecycle database, price optimizer) conflict with a performance grid in the
   harness. Either the non-goals are amended explicitly, or the grid stays with the
   runtime or a gateway and the skill holds only doctrine and state. The author's
   direction implies the first. It is **not** done in this change.
3. **Clusters and effort as part of a model's identity** (§ How).
4. **Renaming `auto`** to `default` (§ What).
5. **Profile consolidation** (§ Profiles and default roles).
6. **A third signal for urgency** (§ Quality, cost, speed and time).

## Open and missing

1. Until this brief is adopted as the spec, the doctrine is stated in several
   places and agrees only by care.
2. **Decorrelation has no resolver and no test** (invariant 5). `decorrelated-from`
   is declared in `skills/biblio-saturation` only; other skills and
   `rules/workflow.md` say it in prose.
3. **Quota-aware routing** has no design, only a question (ticket 0974).
4. **`auto` on Claude Code** has no live implementation; it is a rule.
5. **Traces do not record the requested level.** Where a runtime masks the model
   (Mistral Vibe), even the concrete result is unavailable; the runtime-masked
   identity type landed with PR #1220 (ticket 1038) so the gap is recorded honestly
   instead of reconstructed.
6. **Phase 2 and Phase 5 are unfiled.** `agents/team-lead.md` declares neither model
   nor effort.
7. **No per-runtime statement of model and effort support** exists in
   `adapters/pilot-support.json`. Whether Codex and Pi expose these controls was
   not read for this brief.
8. **No place for time or quota state** in the doctrine today.

## Testable assumptions

Each can fail independently; the reviews should check them one by one.

| # | Assumption | Held how |
|---|---|---|
| A1 | Subagent launches inherit the session model unless pinned (Claude Code) | measured 2026-09-10, one version, one model |
| A2 | Effort controls are not portable across providers | OpenRouter: omitting `reasoning_effort` gave no reasoning while `minimal` enabled it (project memory); not re-measured. Qwen 3.8: more steps and tokens at the same effort label, as reported by the author (arena data not seen here) |
| A3 | Concrete model names change faster than orchestration doctrine | asserted |
| A4 | A different family or vendor reviews with lower correlation than the same family | cited from literature, not measured here |
| A5 | A stronger model at moderate effort beats a weaker one at extreme effort | asserted in the spec; the tournament varies effort inside arms. Tension: Qwen 3.8 defaults to long thinking to make up for size (author, 2026-10-06), a weaker-model-at-high-effort strategy by design |
| A6 | Runtimes will keep or grow their own routers, so IDH should override `auto` only with task knowledge | stated as a trajectory ("modern runtimes increasingly…"), no source cited |
| A7 | A one-shot `frontier` call at standard effort on a deep, well-defined problem pays for itself against repeated attempts at a lower class | author-stated; no measurement |
| A8 | Quota, not price, is the binding constraint on subscription plans | author-stated 2026-10-05; plan terms change |
| A9 | Judging task difficulty cannot be mechanized well, so the orchestrator must judge | author-stated 2026-10-06; no test |
| A10 | Within a cluster, cost, environment, route state and clock can be resolved by a script without a model | author proposal; not built |

## Review questions

Five reviews, each independent. Each reports with the repository's diagnosis
discipline: observation first, cause held until isolated, a null result not counted
until a positive control fired. Each reads this brief at a recorded commit.

(Answered 2026-10-08: no, retired.) **Q0 (key question): are `model-level` and `effort` the right levers?** Effort
levels and the meaning of "default" are not standardized across providers, and a
capabilities, speed and cost scoring is being finished (author, 2026-10-06; its
source and results are not in the repository). Compare four designs: the two
controls as they are; clusters with a script choosing the variant; effort as a
trait of model identity; and adding an urgency signal. For each, say what it needs
in a grid, what it does for blocked routes and time of day, and which non-goal it
breaks. Output: a recommendation with its price in agent cost and author hours.

**R1: doctrine versus the state of the art.** How do published and production
systems route between models (cascades, learned routers, cost-aware selection,
mixture patterns), and which of A4, A5, A7, A9, A10 does the literature support,
contradict or leave untested? Output: per assumption, evidence for and against with
citations; routing ideas the doctrine ignores; and a verdict on the external LLM
router the project did not try.

**R2: doctrine versus provider and runtime trajectories.** For Claude Code, Codex,
Pi, Mistral Vibe, OpenRouter, llama.cpp and Strata: what do current documentation
and release notes say about built-in routing, subagent model selection, effort
controls, quota plans and model deprecation; which of A1, A2, A3, A6, A8 does each
confirm or break; what changes within a year? Output: per runtime, a table of the
assumptions it supports, with dated sources. Facts older than three months are
flagged stale. Fill the portability table's empty cells or mark them unknown.

**R3: implementation versus doctrine.** Start from § Open and missing and verify,
do not trust, these checks:

- do `agents/*.md` frontmatter tokens (`model: standard`, `model: strong`) mean
  anything to Claude Code, or fall through to inheritance? (the cheapest probe);
- which agent profiles set `effort:` (none found by grep on 2026-10-06);
- where `auto` resolves on each runtime in practice;
- does any skill pair `frontier` with `intensive`, or use `frontier` outside the
  three one-shot cases, or default any orchestration to `intensive`;
- the invariant table in ticket 0974;
- the profile and role-table mismatches listed in § Profiles and default roles.

**R4: implementation versus ten historical sessions.** Pre-register before reading:
the ten sessions, the questions and the pass criteria are fixed first, as the
attribution design fixes its statistics first.

- *Sample:* ten sessions across at least three runtimes and at least four projects
  (this harness, climate-finance-het, chemin-de-voix, a manuscript repository, erg
  or equivalent), covering executor, team-lead, reviewer and advisor roles. State
  the selection rule; random draws within strata, not hand picking. Stratify so
  Vibe, whose model is masked, is present.
- *Evidence channel:* on Claude Code, each child records its own effort in
  `~/.claude/projects/<proj>/<session-id>/subagents/agent-<id>.jsonl` with the
  sibling `.meta.json` naming `agentType`. Channels for Codex, Pi and Vibe are not
  established; establishing them is part of the work, and a session whose model
  cannot be read is a recorded unknown, not excluded.
- *Per session:* what was declared; what actually ran (model, effort); whether an
  expensive setting was inherited rather than chosen; whether any `frontier` use fits
  the one-shot condition and any `intensive` use is justified by its cost; whether a
  route was blocked or near its quota and what the launch did about it; whether a
  reviewer was decorrelated from its producer, with the basis; the resulting cost,
  labelled measured or derived.
- *Confidentiality:* extracts may hold uncleared material. Per-session content is
  not committed; only aggregates and anchors go into the repository, the same
  boundary `skills/trace-doctor` keeps. Anything uncleared enters as age ciphertext
  through the project's capture mechanism.
- *Output:* a table, one row per session, the unknowns counted, and no conclusion
  drawn from ten sessions beyond "present or absent in this sample".

**Reviewer independence.** Request reviewers decorrelated from the Claude family
that wrote this brief where the runtime offers one, record the actual identity and
route from runtime evidence, and name any unavailable perspective.
