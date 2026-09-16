---
name: project-gpt-oss-family
description: gpt-oss-* models classify into the gpt family despite being open-weight; family-based splits need explicit subtitle care
metadata: 
  node_type: memory
  type: project
  originSessionId: e1133e47-1abb-4583-b75d-605d3f3d25f5
---

`model_family("gpt-oss-120b")` and `model_family("gpt-oss-20b")` both
return `"gpt"`, alongside `gpt-5.5`. This is the right call for
architectural-family colour grouping (palette stability across
size tiers), but it means any panel split or commentary phrased as
"closed-source frontier" vs "open weights" will misclassify these
two models.

**Why:** Caught during the cost × quality 2-panel split (PR a61a3f2..d1fe235).
The "(a) Closed-source frontier" / "(b) Open-weight" subtitles I first
proposed for the Imagine-mode design were wrong because of gpt-oss-*.
Resolved by using neutral panel labels: `(a) Claude / GPT / Mistral`
vs `(b) Qwen / DeepSeek` (geographic/architectural rather than
license-based).

**How to apply:** When splitting Experiment 1 / 2 / 3 figures by
family, do not call panel A "closed-source" or panel B "open-weight"
unless gpt-oss-* are explicitly excluded or moved. Use family
enumeration (a) Claude / GPT / Mistral / (b) Qwen / DeepSeek, or
geographic framing (Western / Chinese), or licensing if you actually
filter by `requires_oss_filter()`. See `aedist.util.model_family` for
the canonical mapping.
