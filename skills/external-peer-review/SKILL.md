---
name: external-peer-review
description: "Obtain independent external frontier-class peer reviews of a manuscript PDF; synthesize convergent findings into one verdict."
user-invocable: true
disable-model-invocation: false
argument-hint: "<pdf-path> [reviewer needs or personas]"
---

# External peer review

Obtain actual independent reviews and present a cross-reviewer synthesis.
This complements the simulated panel in `/review-pr-prose`.

1. **Locate the manuscript.** Resolve the PDF path and any requested review
   questions. If needed, use the project's build procedure to obtain the PDF.
2. **Describe the reviewers needed.** Request independent advisors with the
   relevant expertise (deep judgment; pick per the `route` skill).
   Prefer reviewers decorrelated from the producer and from one another.
   Personas such as a skeptical expert and an attentive student can diversify
   questions; they do not establish model independence by themselves.
3. **Let the runtime discover and route.** The runtime determines available
   reviewers and the route: llama.cpp on Padmé, OpenRouter, local agents, or
   agents on another host. No gateway, fixed roster, model ID, or transport is
   required. Honor any user constraints on where the manuscript may be sent.
   If no suitable reviewer is available, report that limitation without
   presenting a simulated review as an external one.
4. **Smoke-test one review, sequential-blocking.** Confirm that the selected
   reviewer receives the complete manuscript and returns a non-empty review.
   Use the runtime's available mechanism. The bundled OpenRouter helper is
   optional; read `references/openrouter.md` only when that route is selected.
5. **Collect the remaining reviews, parallel-background when supported.**
   Independent reviewers can work concurrently. Record completed and missing
   reviews, reviewer identities, route, persona, and input coverage in durable
   artifacts. Failed requests remain missing rather than implicit approval.
6. **Synthesize every completed review.** Present consensus verdict, convergent
   concerns weighted by independent support, and sharp individual catches.
   Preserve dissent and attribute findings to the reviewers that supplied them.

Reviews are advisory input for the author. This skill produces review artifacts
and does not publish or merge anything.
