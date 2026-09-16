---
name: feedback-coauthored-rejection
description: Co-authored texts are rejected from voice corpora — mixed-voice signal corrupts style training
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0ee486fd-2869-4fa9-b977-37cc8832b705
---

Co-authored texts must be rejected from voix-* corpora. Mark with `rejected: co-authored` in corpus-inventory.yaml.

**Why:** Co-authored works produce a mixed-voice signal — we can't attribute prose style to a single author, which defeats the purpose of per-figure voice corpora for LoRA training.

**How to apply:** When evaluating new sources, check the author field. If multiple authors are listed, mark the source `rejected: co-authored` and do not fetch/extract it. Remove any downstream files (clean/, clean2/, chunks/) if already processed. Applies to all voix-* figures, not just Manne. See also [[feedback-lora-use-rights]].
