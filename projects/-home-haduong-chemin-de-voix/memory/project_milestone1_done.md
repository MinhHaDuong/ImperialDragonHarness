---
name: project-milestone1-fetch-phase-done
description: Milestone 1 complete 2026-05-14 — all 14 voices ≥ 100K tokens; fetch phase closed
metadata: 
  node_type: memory
  type: project
  originSessionId: 83001c2f-2da2-4822-9ed4-1b9adca2a799
---

Milestone 1 ("Sufficient dataset to train all voices") closed 2026-05-14. Ticket 0013 closed.

All 14 voices are above the 100K robust LoRA threshold (CJK-corrected count):
- Weakest: voix-zhenghe at 133K (appeared as 4K before CJK fix), voix-curie at 148K
- Strongest: voix-auteur at 4.1M, voix-heloise at 1.1M, voix-ada/indy/leonardo ~1M each
- voix-zhenghe now has all 3 steles at authenticity=4 (Changle, Liujiagang, Galle 1409)

**Why:** CJK token counting was silently wrong (wc -w); the fix revealed the corpus was already training-ready. Galle stele (布施錫蘭山佛寺碑) manually fetched from zh.wikisource.org and added.

**How to apply:** Next milestone is 2 (all voices trained). Ready tickets: 0015 (pipeline pilot on voix-auteur), then 0016 (sweep × 14 voices). Unblock 0016 depends on 0015 completing.
