---
name: slides
description: "Make or review a talk's slide deck: build a beamer deck from a written text, or critique an existing deck with prioritized fixes. Keywords: diaporama, présentation."
disable-model-invocation: false
user-invocable: true
argument-hint: "make <source-text> | review <deck>"
---

# Slides

Two modes; a run uses one. **Read that mode's reference before acting.**

- `make` — turn a paper, report or notes into a deck for a talk:
  `references/make.md`.
- `review` — diagnose an existing deck (PDF, ODP or anything LibreOffice
  opens) and return prioritized fixes: `references/review.md`.

No mode given: a deck path means `review`, a text path means `make`.

**Doctrine** lives in `rules/doctype/slides.md`. It loads on a `.tex` edit,
not on a PDF review: read it explicitly in both modes. Its bullets are the
make-mode spec and the review-mode checklist; neither reference restates them.

**Upstream.** A deck has one central message. If the author cannot state it
in a sentence, run `/message-framing` first; neither mode invents it.

## Render and look

Both modes end on pixels, never on source. Convert a non-PDF deck with
`soffice --headless --convert-to pdf <deck>`, then
`pdftoppm -png -scale-to-x 1200 <deck>.pdf page` and look at every page
image, sequentially in one context: consistency is a judgment across pages,
so there is no fan-out. **Never announce a deck done, or a review complete,
without having looked at the rendered pages.**
