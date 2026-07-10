---
name: user-moa-moe-contract
description: "Working contract — user is MOA (owner, decides what/why), Claude is MOE (orchestrates agents of appropriate complexity/effort)"
metadata: 
  node_type: memory
  type: user
  originSessionId: 91082cef-1957-4b31-8155-3333fc2cc566
---

Established 2026-07-08: the user frames collaboration as maîtrise d'ouvrage / maîtrise d'œuvre. He is MOA — defines needs, budget, priorities, and accepts delivery (merges). Claude is MOE — designs the solution and orchestrates execution by delegating to subagents sized to the task (light models for mechanical work, cross-model review, top tier for hard design), within existing harness rules (one well-prompted agent first, max 8 concurrent, worktree + PR discipline).

**How to apply:** Default to delegation-with-rightsizing rather than doing everything inline; report design decisions and deviations to the user, not execution noise; surface better approaches before acting. See [[feedback_decide_dont_micromanage]].

**Review triage (author correction 2026-07-08, « c'est que des jugements mécaniques là, je fais pas ça »):** never hand the MOA mechanical judgment calls (YAML plumbing, anchor refs, term-consistency, ratchet workarounds) — those are MOE work: settle them, or route them through the verification loop (/gaze). The author's review of a deliverable is voice and meaning only. A "judgment call for the author" must pass the test: does answering it require being the author?

**Model ladder (author reminder 2026-07-08): four tiers — Haiku → Sonnet → Opus → Fable.** Haiku for mechanical lookups, Sonnet for searches/inventories/reviews, Opus for complex coding and cross-model review, Fable for the hardest design and author-voice prose (e.g. the style-anchored manuscript translation). Pin `model` per launch; reviewers below the producer tier.

**Don't block a deadline on model availability (author, 2026-07-08).** When Fable is unavailable (out of credits until next week) the author chose to ship the Œconomia R&R now on Opus rather than wait. Rationale: Fable's edge is voice-anchoring, not correctness; the review panel catches the factual/citation slips Opus prose introduces (it caught Jachnik/Ellis + ETF/SBSTA on Act III), and 0134 is the author's own human-led voice pass anyway. So: proceed on Opus for author-voice prose (conclusion 0171, title 0181) when Fable is out, compensate with heavier review scrutiny, and let the author's final pass restore voice.
