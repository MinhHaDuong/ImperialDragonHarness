---
name: sota-parser-quirks-per-model
description: "Each new SOTA model in the fan-out brings format quirks (em-dash, Roman, bare 1)) — parser strategies multiply reactively"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f58bf9dc-2a2d-4bf2-8f52-d1c99dbb3d89
---

When adding a new model to the SOTA fan-out (generate_sota.py), expect new parser quirks in its output for the partis-pris / translation format. Recent additions to `scripts/extract.py`:

- Strategy C: split on `\d\)` (most models)
- Strategy D: split on `Traduction\s+\d+` (gpt-5 vanilla on hcm/leonardo emits both bare `1) Label` for listing AND `Traduction N — Label` for translations — C wrongly splits the listing)
- `_HEADING` regex now accepts `—`, `–`, `-` alongside `.`, `)`, `:` (Opus 4.6 auteur)
- Roman numeral headers (`## I – Distiques`) — separate fix (#140)

Best-of-4 selection now compares parsed_a/b/c/d and keeps whichever yields most distinct parti_pris numbers, so a new strategy doesn't have to win on every voice.

**Why:** Format detection is reactive — a failing case prompts a new strategy. PRs #140, #142 each added one. Pattern will repeat for the next model family.

**How to apply:** Before running a full fan-out with a newly-added model, parse 1–2 sample outputs first and check `parsed_a/b/c/d` distinct-parti-pris counts. Cheaper than discovering at aggregate-voice time.

Related: [[parse-chunk-headers-blank-lines]] for an earlier parser bug class.
