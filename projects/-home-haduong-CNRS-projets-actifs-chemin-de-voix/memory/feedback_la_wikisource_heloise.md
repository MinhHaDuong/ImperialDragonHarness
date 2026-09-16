---
name: la-wikisource-heloise
description: "Héloïse's Latin letters are at Scriptor:Heloisa on la.wikisource.org — NOT Epistolae_(Abaelardus) which is a citation index only"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a35f7c24-d6a7-4938-99a5-8e7811affaeb
---

Correct URLs for Héloïse's Latin prose on la.wikisource.org:

- Author page: `https://la.wikisource.org/wiki/Scriptor:Heloisa`
- Letter I: `https://la.wikisource.org/wiki/Epistula_ad_Abaelardum_I` (50% transcribed, ~15KB)
- Letter II: `https://la.wikisource.org/wiki/Epistula_ad_Abaelardum_II` (50% transcribed, ~16KB)
- Problemata: `https://la.wikisource.org/wiki/Problemata_Heloissae` (150KB — Héloïse's questions + Abelard's SOLUTIO; take the whole file, LLM extracts only Héloïse's voice)

**Why:** Previous attempt used `Epistolae_(Abaelardus)` and `Epistolae_(Heloissa)/Epistola_II` — both 404 or bibliography-only. The correct author page is `Scriptor:Heloisa` (not `Auctor:`).

**How to apply:** When fetching via `action=raw`, use `?title=Epistula_ad_Abaelardum_I&action=raw`. Strip wikitext: extract content between the two `{{Liber...}}` navigation blocks.
