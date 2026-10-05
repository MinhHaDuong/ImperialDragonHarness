# Runtime-routed live review

## Request and discovery

Give the active runtime the reviewed repository, PR (when applicable), exact
base and head revisions, accessible review material, expertise, capability
class and independence requirement. Resolve repository paths explicitly; a
helper's own checkout is not necessarily the project being reviewed. Include
the question to answer and a bounded completion deadline. Request only the
material and access needed for review; preserve read-only containment and never
include credentials in prompts, logs or evidence.

Discover available routes at runtime. llama.cpp on Padmé, OpenRouter, other
local agents and agents on another host are possible resources. An unavailable
endpoint or helper does not exhaust discovery; try a suitable available route
within the budget. No roster, subscription or particular gateway is a
prerequisite. Discovery and routing do not authorize purchases or configuration
changes. Use an existing helper only when its access and containment suit the
review material.

Choose a reviewer decorrelated from the producer when available. Record the
actual reviewer identity (model/version and provider when exposed), route,
independence basis and limitations from runtime evidence. Never infer a model
identity or independent review from a configured name, requested model or
successful dispatch alone. A separate process with the same model is not
provider or model independence; identify unavailable perspectives explicitly.

## Findings and provenance

For every requested review, retain the request, exact reviewed revisions,
completion status and returned evidence, with an accessible artifact or forge
comment link. Distinguish a completed review with zero findings from one that
never ran. If revisions change, label the earlier review stale and obtain
review of the current material before claiming that it covers the new head.

Pass actual findings to the gate using its existing classes:

```
verifiable: <file>:<line> — <rationale and supporting evidence> [reviewer]
consider: <file>:<line> — <rationale> [reviewer]
```

Keep the raw report and its provenance alongside normalized findings. Surface
unparseable output as a WARN with the raw evidence; never silently drop it or
invent a clean verdict. The gate dispositions external findings like internal
ones: verifiable findings may bounce; suggestions are noted-not-blocking.
Optional participation does not waive a real finding.

## Availability and integrity

Record failures separately from findings, using the existing report markers:

```
SEAT-FAILED: <reviewer or route> — <observed failure> [did NOT review]
SEAT-MISSING: <requested perspective> — <no completed evidence> [did NOT review]
PANEL-INTEGRITY: <missing or failed perspectives> — review coverage incomplete
```

An error, timeout, missing access or absent reviewer is a visible limitation.
Carry integrity records verbatim into the review report; do not disposition
them as findings. Optional external evidence is fail-open: WARN and proceed
with the required internal battery and gate. An empty result without a
completion record is unavailable evidence, never a clean review.

When a permission denial specifically requires independent evidence, this
fail-open policy cannot cure the objection. Only actual completed independent
review of the current material, with its findings dispositioned, can support
one retry under the caller's recovery contract. If that evidence is unavailable,
park the merge and report the limitation; never bypass the permission layer.
