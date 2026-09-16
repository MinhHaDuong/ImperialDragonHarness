---
name: ada_corpus_byron_weighting
description: voix-ada corpus is 97% Byron (analogue) — training must weight Ada's own 44K tokens heavily
type: project
originSessionId: dabd1750-4d3a-468f-8222-0138a55d1233
---
After Byron enrichment (night raid 2026-05-09), voix-ada/raw/ has ~1.09M tokens
but only ~44K are Ada's own writing (Menabrea translation + Notes A–G). The rest
is Byron (Childe Harold, Don Juan, Letters/Journals ×2, Early Poetry).

**Why:** Ada has almost no surviving prose. Byron added as voice-enrichment analogue.

**How to apply:** When executing 0016 Ada split/launch phases, the style-strength
score (ticket 0070) will rate Ada's own work score=8 (authenticity=4, genre=2,
decon=2) vs Byron score=6 (authenticity=2). At 2× training budget, Byron score=6
passes the threshold=5. At 5× budget, threshold=7 would drop all Byron. The
training dataset should consciously over-represent Ada's 44K tokens — consider
repeating Ada passages or using a very high richness ratio threshold for Byron.
