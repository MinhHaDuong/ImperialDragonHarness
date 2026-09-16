---
name: pandoc-docx-span-character-styles
description: "Pandoc DOCX writer maps inline spans to character styles only via the `custom-style=\"...\"` attribute — bare class names like `.verse-num` are silently ignored"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff1f28d7-df07-4e2e-8181-0eb5c4a6e448
---

When mapping a Pandoc inline span to a Word character style defined in your
reference.docx, use `[text]{custom-style="style-id"}` — NOT `[text]{.style-id}`.
Bare class syntax is silently dropped at DOCX render time; OOXML inspection
shows zero `<w:rStyle>` references.

**Why**: Found by writing 95 `[N]{.verse-num}` spans in a Pandoc 3.1.3 → DOCX
pipeline and counting zero `<w:rStyle w:val="verse-num">` applications in the
output. Switching to `[N]{custom-style="verse-num"}` got 95/95. The reference
docx had the style correctly defined (`w:styleId="verse-num"` + matching
`<w:name w:val="verse-num"/>`) — the markdown syntax was the only difference.

**How to apply**: For any Pandoc DOCX project where you want span-level
character styling (small caps, color marks, annotations like verse numbers),
always use the `custom-style="..."` attribute form. The class syntax `.foo` is
useful for HTML output and div-level paragraph styles, but not for inline
character runs in DOCX.

See [[prototype-docx-pipeline]] for the broader DOCX pipeline gotchas.
