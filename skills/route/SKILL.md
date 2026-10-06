---
name: route
description: "Model routing: performance grid, route cache, triage, clusters. The single home for which model serves which work."
disable-model-invocation: false
user-invocable: false
---

# Route — routage des modèles

`[Grid → Triage → Decision]`

This skill owns three things, and they live nowhere else: the performance
grid (which model is worth what, at explicit effort levels), the route-state
cache (`routes.json` beside this file — which doors are alive, at what caps
and prices), and the two-stage routing decision (cluster by task, then
model by cost and environment) that decides where a piece of work goes
before any expensive model touches it.

## Update discipline

- The grid changes ONLY from arena cycle data (skills/arena) or an explicit
  author-run test — never from vibes, provider marketing, or bench claims.
- Mid-cycle: the grid may show a cycle's provisional numbers marked
  `provisional`; they are not routing-grade until the cycle closes.
- After each cycle: refresh the grid AND `routes.json` (status, prices, caps,
  `last_verified`), in the same pass as the cycle verdict.

## Performance grid

Costs are per leg on the arena sample (11 tickets). Locals pay electricity
(0.23 EUR/kWh x 600 W, registered 2026-10-06); hosted pay the API
(pi cost.total, component-priced).

The grid lives in `grid.json` beside this file (data, not portable
instructions — the model-rightsizing policy keeps concrete model names
out of SKILL.md). Read it for quality/speed/cost per identity and the
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

## Two-stage routing: cluster by task, then model by cost and environment

Stage 1 — the TASK picks the CLUSTER (triage above feeds it). Stage 2 —
COST and ENVIRONMENT pick the MODEL inside the cluster. Clusters derive
from the grid (arena cycles only); membership moves only with new cycle
data.

Cluster membership lives in `grid.json` (`clusters` key) — data, not
portable instructions.

*VOID-EMPTY pattern: the OR cheap flashes abandon heavy tickets silently
(GLM-flash, Mimo: empty diffs on 0452/0874/1372) — inside-cluster selection
must check ticket weight, not just price.

Within-cluster selection keys: cost per leg (grid above), latency, and
environment: privacy/clearance (forces LOCAL/PRIVÉ), offline, GPU idle vs
the local lane busy, provider rate limits. Within ÉCONOMIQUES, Luna is the
default absent a reason; within LOCAL/PRIVÉ, IQ3_S for quality, Q2_0 for
speed on non-judgment tickets, 27B for vision.

Cluster-by-task examples (triage output → cluster): smoke/routine →
ÉCONOMIQUES; concrete implementation → MILIEU SOLIDE; judgment/consistency
or monster → ASSURANCE; uncleared content → LOCAL/PRIVÉ; ambiguous →
need-human before any spend. The 256K guard outranks all stages: oversize
context is a split-the-work ticket, never a bigger-window ticket.

## routes.json

Cache of the doors: provider, endpoint, key name (names only — never values),
status (live / dead / capped), price notes, caps, last_verified. Update it
whenever a route changes state — the 2026-10-06 session showed why: a free
endpoint can die overnight (SpaceBunny 404) and a billing wall can drop
mid-pass (OpenAI "no credits remaining"). Routing on a stale route cache
burns attempts and money.
