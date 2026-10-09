---
name: reviewers
description: "Describe live independent review needs and let the active runtime discover and route optional reviewers, preserving findings and integrity evidence."
disable-model-invocation: false
user-invocable: true
argument-hint: "<review material> [expertise and independence needs]"
---

# Live reviewer routing

Describe the review material, required expertise and
independence needs to the active runtime. Let it discover available reviewers
and choose a route. Read `references/live-route.md` before routing or collecting
evidence; it defines the request, result and unavailable-review contracts.

Possible resources include llama.cpp on Padmé, OpenRouter, other local agents,
and agents on another host. Use available helpers when useful. These are
optional routes, with no mandatory provider, transport or preference order.
Record the reviewer and route actually used, the material reviewed, the returned
findings and any unavailable perspective. Optional external review is fail-open;
unavailable evidence must remain visible and must never count as approval.

For read-only replay of the frozen, already merged benchmark board, use
`skills/coaching/SKILL.md` (`/coaching`). Live routing does not manage trial
records or reviewer promotions.
