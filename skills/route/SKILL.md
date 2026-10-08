---
name: route
description: "Model routing: performance grid, route cache, triage, clusters. The single home for which model serves which work."
disable-model-invocation: false
user-invocable: false
---

# Route — routage des modèles

`[Grid → Triage → Choice]`

This skill owns three things, and they live nowhere else: the performance
grid (which model is worth what, at explicit effort levels), the route-state
cache (`routes.json` beside this file — which doors are alive, at what caps
and prices, plus how each runtime launches a worker), and the guidance an
orchestrator uses to choose a worker before any expensive model touches the
work.

## Update discipline

- The grid changes ONLY from arena cycle data (skills/arena) or an explicit
  author-run test — never from vibes, provider marketing, or bench claims.
- Mid-cycle: the grid may show a cycle's provisional numbers marked
  `provisional`; they are not routing-grade until the cycle closes.
- After each cycle: refresh the grid AND `routes.json` (status, prices, caps,
  `last_verified`), in the same pass as the cycle verdict.

## Performance grid

Costs are per leg on the ten-ticket arena sample; cycles are additive and
each model/effort identity remains distinct. Preliminary smoke runs are excluded. Locals pay electricity
(0.23 EUR/kWh x 600 W, registered 2026-10-06); hosted pay the API
(pi cost.total, component-priced).

The grid lives in `grid.json` beside this file (data, not portable
instructions; model names live in data and in the per-runtime
recommendation files). Read it for quality/speed/cost per identity and the
provisional marks; update it ONLY from arena cycle data.

Effort labels are model-relative, NOT transportable across generations
(Sol 6.1 @medium does more work than Sol 6.0 @medium at the same label).
Therefore the EFFORT LEVEL IS A TRAIT OF THE MODEL'S IDENTITY: the routable
unit is the pair (model @effort), measured as one atomic identity — the
grid rows are identities, not knobs. Consequences:

- Never route to an unbenched (model, effort) pair. Changing the effort
  creates a NEW identity that needs at least a smoke + spot check before
  it enters the grid.
- Always name the effort explicitly; `@default` is banned in labels —
  resolve it to the real level first (pi `defaultThinkingLevel`=medium,
  but the pi CATALOG default wins per model — the DeepSeek and GLM flash
  siblings sit at HIGH, not medium, verified in sessions 2026-10-05;
  grid.json names them).
- The identity's verified level comes from session evidence
  (`thinking_level_change` events), never from the label it was launched
  with.

## Difficulty triage (before routing)

Difficulty is an intrinsic, SEMANTIC property of the ticket: our 16-arm data
shows strong arms correlate 0.83-1.0 on which tickets are hard, while
mechanical metadata predicts nothing (Pearson difficulty vs diff-lines =
0.08; code-large contains both the easiest and hardest tickets). Judgment /
consistency tickets (0874, 0452) are the killers; concrete fixes (0333) and
trivial swaps (0470) are not.

- Triage is an LLM read of title + body + exit criteria, priced in the value
  class (~0.01 $). Mechanical features (stratum, size, files) do NOT
  separate difficulty — do not use them alone.
- The 256K monster guard is a hard floor and stays: oversize context is a
  split-the-work ticket, never a bigger-window ticket.
- Known cheap validators: 0470 is the arena's smoke ticket (fast, fully
  characterized; near-zero variance — it validates infrastructure, it does
  not discriminate models).

## Choosing a worker

The orchestrating model chooses, from the task and its context. No script
maps a level to a model. Inputs:

1. The task, after triage above: what it costs to be wrong, how cheap it is
   to verify, how much context it needs.
2. The grid (`grid.json`): quality, time and cost per (model @effort)
   identity, the `clusters` key as a starting shortlist, and the `family`
   label of each row.
3. The route cache (`routes.json`): which doors are alive, their caps, and
   how each runtime launches a worker (`launch_doors`).
4. The general recommendations below, then your runtime's file.

General recommendations:

- Spend the least that the task tolerates. Smoke, routine, bulk and
  cheap-to-verify work goes to the ÉCONOMIQUES cluster; Luna is the default
  absent a reason, and Haiku 5.5 is its peer inside Claude Code. Keep a
  Haiku worker under 100K prompt tokens (price x5 above).
- Concrete implementation goes to MILIEU SOLIDE; judgment, consistency or
  monster work to ASSURANCE. Uncleared content forces LOCAL/PRIVÉ. Ambiguous
  tasks wait for a human before any spend. The 256K guard outranks all of
  it: oversize context is a split-the-work ticket.
- Choose the lineage on purpose. A reviewer that shares the producer's
  `family` adds replication, not independence. When the risk calls for an
  independent view, take a worker of another family, and say in the report
  when none was reachable.
- Never route to a (model, effort) pair that is not in the grid.

Launch doors. A worker is reached in one of two ways: a subagent inside the
current CLI, or a headless CLI started from bash with a given model. The
exact forms, and which were verified, are in `routes.json` under
`launch_doors`. Pin the model on every launch.

Runtime recommendations. Read the file for the runtime you are running in:

- If you are Claude Code, read `routes-recommendations-claude-code.md`.
- If you are Codex, read `routes-recommendations-codex.md`.
- If you are Pi, read `routes-recommendations-pi.md`.
- If you are Vibe, read `routes-recommendations-vibe.md`.

Model timeouts and admissible empty submissions score zero; include consumed
time and cost, and show completion coverage. Provider/quota errors are invalid
observations pending replay, not evidence of model abandonment. Identities
with pending cases remain provisional and are excluded from final rankings.
Paired comparisons retain model failures and report wins, ties and losses;
an equal median difference does not establish per-ticket dominance.

Within-cluster selection keys: cost per leg (grid above), latency, and
environment: privacy/clearance (forces LOCAL/PRIVÉ), offline, GPU idle vs
the local lane busy, provider rate limits. Within LOCAL/PRIVÉ, IQ3_S for
quality, Q2_0 for speed on non-judgment tickets, 27B for vision.

## routes.json

Cache of the doors: provider, endpoint, key name (names only — never values),
status (live / dead / capped), price notes, caps, last_verified. Update it
whenever a route changes state — the 2026-10-06 session showed why: a free
endpoint can die overnight (a stealth OpenRouter model returned 404) and a billing wall can drop
mid-pass (OpenAI "no credits remaining"). Routing on a stale route cache
burns attempts and money.
