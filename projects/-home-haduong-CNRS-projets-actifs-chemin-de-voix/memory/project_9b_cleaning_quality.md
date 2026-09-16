---
name: 9b-cleaning-quality-gaps
description: Qwen3.5-9B cleaner has systematic failures on verse numbers (alienor) and running page headers (manne); documented in ticket 0144
metadata: 
  node_type: memory
  type: project
  originSessionId: 4c46085b-b879-4ec9-ac09-fb1cd29e9730
---

Corpus-wide diff of `extracted/` vs `cleaned/` (2026-05-15) found systematic artifact survival:

- **voix-auteur**: 2311× bare `Minh` signature fragments, 342× standalone year lines, address fragments in 287 lines
- **voix-manne**: 84% of running page headers survived (`158 Economic Analysis for Business Decisions`…); journal submission metadata (10×)
- **voix-hcm**: running header `Selected Works of Ho Chi Minh - Volume I` (18×), publisher boilerplate (26×)
- **voix-alienor**: 224/906 verse-number lines survived (25% miss rate); 682 correctly stripped
- **voix-curie**: clean — zero flags

Ambiguous cases (may be valid voice signal): feynman letter signatures, ada letter closings, leonardo section numbers, tnh liturgical titles, indy epitaphs.

**Why:** 9B model not explicitly instructed to strip these patterns; some are prompt gaps, some are model-capability gaps (Manne headers). Documented in ticket 0144.

**How to apply:** Before running 0016 sweep, decide: targeted re-clean of auteur/manne/hcm/alienor via OpenRouter (cheap, ~$2-7 total), or add explicit stripping instructions to system prompt and re-run locally. See ticket 0144 for full option matrix. [[ticket 0015 pilot status]]
