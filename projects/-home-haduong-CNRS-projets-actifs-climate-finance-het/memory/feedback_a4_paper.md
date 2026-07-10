---
name: feedback-a4-paper
description: "Always generate PDFs in A4 paper format, never US letter"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8a3dc47b-4c38-4220-b393-129612e7453c
---

Always use A4 paper format for every PDF generated for the author (pandoc,
LaTeX, reports, letters).

**Why:** Author directive 2026-07-10 ("Always use A4 paper format"), after a
pandoc-generated response letter came out in US letter. European academic
context; Œconomia and all French institutions use A4.

**How to apply:** pandoc → `-V papersize=a4`; raw LaTeX → `a4paper` class
option or `geometry`. Quarto project deliverables already configure their own
geometry — this applies to ad-hoc documents I generate (letters, notes,
reports).
