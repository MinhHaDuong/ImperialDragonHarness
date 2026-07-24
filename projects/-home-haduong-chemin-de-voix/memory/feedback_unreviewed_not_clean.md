---
name: feedback-unreviewed-not-clean
description: "Empty polish rules means the voice was audited and no rules were needed — not that it was skipped; but rahan is the one genuinely unreviewed voice as of 2026-05-16"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 345674d2-e23b-4c8c-9a44-2efa24b95106
---

Empty rule lists in `polish_corpus.py` do NOT mean "not yet reviewed." As of 2026-05-16, all 14 voices have been handled:

- **heloise, manne, alienor, hcm, auteur**: rules written or v1.1 re-clean applied
- **ada, feynman, carton-de-wiart**: rules added 2026-05-16 from deferred 0144 audit findings
- **curie**: 5% audit found zero flags — genuinely clean
- **indy, zhenghe**: audit found patterns classified as valid content, no rules needed
- **tnh**: v1.1 re-clean handles former artifacts
- **leonardo**: re-cleaned with gemini-3.1-flash-lite 2026-05-16, 0 rules needed
- **rahan**: spot-checked 2026-05-16 — zero artifacts; all-caps chapter titles are genuine section headings, not navigation artifacts

**Why:** The original mistake was inferring "clean" from "no rules." The corrected state is that empty rules now means "audited and nothing actionable found" for all voices except rahan.

**How to apply:** If reasoning about rahan quality, treat as unknown. For all other voices, empty rules = reviewed. Never collapse the two cases without checking which one applies.
