---
name: local-evidence-gate-for-pillaged-techniques
description: Before implementing a technique pillaged from a paper, inventory whether the defect class it targets actually occurs in the local codebase — 0290 closed wontfix when a 2-suite audit found zero instances.
metadata:
  type: feedback
---

A paper-pillaged tooling ticket (detector, guardrail, audit lens) can survive
filing, ratification, and child-splitting without anyone checking whether the
defect class it hunts exists locally. Ticket 0290 (hardcoded-output-literal
detector, from arXiv:2604.21965 App. B.4) closed wontfix on 2026-07-13 after
two parallel auditors read every assert-against-literal in the IDH and
chemin-de-voix suites and found zero instances — both suites already practiced
the antidotes (eyeball-able inline fixtures, live-config derivation, threshold
assertions, documented canaries).

**Why:** a paper's failure mode is evidence about *its* population (often
LLM-generated code), not about these codebases. Building the detector would
have cost a full ticket cycle to remediate a defect with zero local
occurrences.

**How to apply:** when picking up a pillage-manifest child (or filing one)
whose deliverable is a detector or audit for a defect class, first run a cheap
read-only inventory of the real suites/corpora for that class — a subagent
sweep costs minutes. Zero instances → close wontfix with the evidence in the
ticket body, or reframe to the narrow context where the class does occur
(e.g. a gate on freshly agent-generated tests). Conventions and labels
(like [[0291]]-style taxonomy tickets) are exempt — the gate is for builds
with real cost. See tracker 0266.
