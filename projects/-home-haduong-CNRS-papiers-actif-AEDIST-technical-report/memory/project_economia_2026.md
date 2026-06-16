---
name: econom-ia-2026-presentation
description: "Econom'IA 2026 talk delivered 2026-05-27 (tag economia-2026-cergy, HAL hal-05644906); technical report diffused 2026-06-15 (tag economia-2026-report, 2da83d04) and deposited on HAL 2026-06-16 as working paper hal-05658462"
metadata: 
  node_type: memory
  type: project
  originSessionId: deab15ae-916a-4088-89c1-cfb8a32815c8
---

AEDIST findings presented at Econom'IA 2026 on 2026-05-27 (Cergy/Thema), Beamer deck in French —
but the talk was *delivered in English* (author's correction; never write "as presented in French").
Deck title: *Beyond RAG: Architectures for Reliable Economic Statistics with Agentic Systems*.

Archived 2026-06-04 (ticket 0412): the presented version is commit `bbc4a013`, tagged
`economia-2026-cergy` (anchor verified by diff — no deck-relevant change between that
commit and the first post-conference revision). GitHub release carries the rebuilt PDF.
HAL deposit: [hal-05644906](https://hal.science/hal-05644906). Personal page entry in
`~/CNRS/html/src/Ha-Duong.bib` (`Ha-Duong2026:economia`).

**Why:** Slides figures change after fix1/v2 reference adoption (0413) — the tag preserves
the exactly-presented state.

**How to apply:** Any question about "what was shown at Econom'IA" resolves against the tag,
not main. Paper writing follows; the EN deck (`slides-en.tex`) post-dates the talk.
[[project-exp1-module-scheme]]

**Follow-up — technical report diffused to participants (2026-06-15):** the full
manuscript (`slides/manuscript/main.tex`, title *Can Frontier AI Build a Statistical
Register? A Benchmark and Research Programme on Vietnam's Thermal Power Fleet*) was sent
to the conference organizer for diffusion to Econom'IA 2026 participants. The diffused
PDF is commit `2da83d04`, tagged **`economia-2026-report`** (65 pages, widow-free,
peer-review-calibrated). **HAL deposit 2026-06-16 (ticket 0664):** a *separate* HAL
record [hal-05658462](https://hal.science/hal-05658462) — type `UNDEFINED`
(Preprint/Working paper bucket; HAL SWORD rejects the `WORKINGPAPER`/`UNDERTAKING`
leaf codes, only the top-level is accepted), CC-BY 4.0, `seeAlso` cross-links to the
talk record hal-05644906 + the GitHub release tag. Deposited via the `/update-publist`
SWORD path (Content-Disposition filename must be the meta `*.xml`, not the zip). NOT
merged into the talk record (no double counting: slides=COMM, report=working paper).
Pending moderation at deposit time. arXiv transfer (0665) deliberately deferred to the
planned v2 article (this version is a working paper, not the final preprint). Before
that send the manuscript went through: a 4-reviewer
external panel (OpenAI gpt-5.5 + Mistral large, grinchy + student personas, via the
`/external-peer-review` IDH skill) → tracker ticket 0644 (9 prose findings fixed, 8
experiments deferred post-arXiv, 0653 related-work expansion declined) → front-to-back
pagination shaving (abstract/intro/§7/§9/§10 widows cleared, conclusion landing on
page 26). Reviews archived under `slides/manuscript/attic/peer-reviews-2026-06-15/`.
