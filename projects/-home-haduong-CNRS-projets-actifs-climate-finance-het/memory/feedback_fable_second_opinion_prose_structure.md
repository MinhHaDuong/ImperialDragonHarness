---
name: feedback-fable-second-opinion-prose-structure
description: "Asking Fable (independent model) for opinions on manuscript structural TODOs produced concrete, actionable, section-specific recommendations"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8be8f7a-2eb1-4c58-ba7b-8c8397fc6d6c
---

Spawning an `Agent` with `model: fable` to review a batch of inline
editorial TODO markers (e.g. "[MOVE THAT PARAGRAPH LATER]", "[REWRITE
PARAGRAPH...]", "### PROBLEM SECTION: CULL, REHOME IDEAS?") in the
Œconomia manuscript worked well as a decorrelated second opinion, worth
repeating for future structural-editing passes.

**Why it worked**: giving Fable the full surrounding prose context per
TODO (not just the bracketed note) let it recommend concrete actions —
trim vs. move vs. cut, with a drafted replacement paragraph for one
rewrite request — rather than generic advice. It correctly flagged that
one TODO ("streamline the flow order") was only half-satisfied by an
earlier pass (subsection headers were added, but post-2015 material had
leaked backward into the 2007-2014 section) and caught a real citation
bug (`dimaggio1983` missing its `@`) along the way.

**How to apply**: for future manuscript restructuring where the author
leaves themself several structural TODOs to resolve later, batch them
into one Agent call with `model: "fable"`, include full paragraph
context (not just the bracket text) and the article's core argument/
periodization, and ask for a recommendation + reasoning per item plus
an overall verdict on section readiness. See
[[project_background_session_manuscript_pr_workflow]] for the concrete
session this was used in (2026-07-16, Crystallization section TODOs).
