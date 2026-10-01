---
name: reference_snake_case_index_tokenizes_dense
description: "A MEMORY.md index costs ~2.4 bytes per token, not 4: snake_case filenames tokenize densely, so bytes/4 underestimates it ~1.7x"
metadata:
  type: reference
---

Measured by `/context` on 2026-10-01: climate-finance-het's MEMORY.md, 10.4 KB, cost 4.4k tokens (estimate by bytes/4 was 2.6k). Byte split of the 101 entries: filenames ~40%, titles ~36%, hooks ~13%; filenames dominate even more in tokens. Shortening hooks saves little; fewer entries, or shorter slugs (a scripted rename that keeps `[[links]]`), are the levers. Measure with `/context`, never bytes/4. Related: [[feedback_derived_token_figures_must_be_swept]].
