---
name: feedback-verify-ai-generated-includes
description: "Never cite or reuse content from an \"AI-generated, not human-reviewed\" include without verifying its attributions — one contained a phantom reference"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8a3dc47b-4c38-4220-b393-129612e7453c
---

Never cite, quote, or build an argument on content from a techrep include
marked "AI-generated, not human-reviewed" without first verifying its
attributions and numbers against resolvable metadata.

**Why:** 2026-07-10 (ticket 0152): `bibliometric-context.md` (§11) contained a
PHANTOM reference ("Baran et al. 2024" — no such paper; the real study is
Rusydiana 2023), a wrong corpus size (657 vs 2,311), and a false claim ("none
report validity metrics" — the CiteSpace studies do). Web-verifying all four
named studies took one agent run; the errors would otherwise have reached a
response-to-reviewers letter.

**How to apply:** before using such an include, resolve every author-year
attribution via CrossRef/DOI (agent run), trace pipeline numbers to archived
outputs, and correct in place with a dated provenance comment. Ticket 0244
tracks the four remaining unverified includes. Related: [[feedback-read-before-cite]].
