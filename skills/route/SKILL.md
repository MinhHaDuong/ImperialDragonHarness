---
name: route
description: "Model routing for harness work: performance grid, route-state cache, and difficulty triage. The single home for which model serves which work — never dispersed into other harness rules."
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

Cycle-1 FINAL / cycle-2 PROVISIONAL (backlog of judging pending):

| model (effort EXPLICIT) | qual /30 | time | $/leg | role |
|---|---|---|---|---|
| Opus 5.5 @medium | 23.7 (c1) | ~10 min | ~2.2 | consistency buyer — the only arm without a crater; hard/monster work |
| FlashNext IQ3_S @xhigh (local) | ~27 (c2 prov.) | 43 min | 0.11 elec | best local quality; privacy; big-ticket survivor (18/30 on the killer ticket where Sol cratered) |
| Sol 6.1 @low | ~24.5 (c2 prov.) | 6 min | 0.20 | solid mid hosted |
| Luna 6 @medium | ~23 (c2 prov.) | 4 min | 0.03 | DEFAULT WORKHORSE for routine work; beats Sol 6.0/6.1@medium on efficiency, no crater observed |
| 27B @xhigh (local) | ~24 (c2 prov.) | 48 min | 0.12 elec | daily local seat + vision niche |
| GLM 5.3 @high | 21.6 (c1) | 9 min | 0.52 | — |
| Sonnet 5.5 @medium | ~21.5 (c2 prov.) | 1 min | 0.11 | fast hosted filler |
| Coder IQ1_M @xhigh (local) | 21.1 (c1) | 31 min | 0.08 elec | — (false-completion risk) |
| 35B-A3B / Coder-30B @tpl (local) | 9-10 | <7 min | 0.02 elec | FALSE-COMPLETION family — never route real work here |
| Opus 5.5 @low | ~20.5 | 3 min | 0.44 | NOT worth it: pays Opus prices, delivers Sonnet-tier with craters |
| OR cheap flashes (GLM-flash, Mimo, SpaceBunny) | mixed | — | 0.06-0.17 | VOID-EMPTY on heavy tickets — silent abandonment; cheap routine only, with a liveness check |

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
  but the pi CATALOG default wins per model: deepseek-flash and
  glm-5.3-flash sit at HIGH, verified in sessions 2026-10-05).
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

| cluster | members (effort explicit) | when the task says |
|---|---|---|
| ASSURANCE (no-crater allowed) | Opus 5.5 @medium | high stakes, monster tickets, work where a silent failure costs more than the call |
| MILIEU SOLIDE | Sol 6.1 @low/@medium, Sonnet 5.5 @medium, GLM 5.3 @high | real implementation work, judgment-heavier than routine, hosted is fine |
| ÉCONOMIQUES | Luna 6 @medium (default), DeepSeek 4.1 Flash @high, GLM 5.3 Flash @high*, Mimo @medium* | routine work, cheap to verify, bulk triage |
| LOCAL / PRIVÉ | FlashNext IQ3_S @xhigh, FlashNext Q2_0 @xhigh, 27B @xhigh | uncleared content, offline, GPU-bound work |
| BANNIS | 35B-A3B, Coder-30B (false-completion); OR flashes on heavy tickets* | never route real work here |

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
