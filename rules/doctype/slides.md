---
paths:
  - "**/*.tex"
last-reviewed: 2026-10-01
---
# Slides

Document-type conventions for any talk deck; beamer is the default source,
ODP or PPTX a LibreOffice conversion of its PDF. Language norms live in
`lang/`, universal prose in `prose/_all.md`; procedure in the `/slides` skill.

- **One talk, one message.** Every slide serves it; a slide that serves another message goes, however good.
- **One idea per slide.** A slide that turns is two slides.
- **The title states the takeaway**, not the topic: "Warming doubles retrofit cost" beats "Results". Two lines at most.
- **The titles alone tell the argument.** Read in sequence, they state the message; if the slides could be shuffled unnoticed, there is no thread.
- **Fragments, not paragraphs.** Full sentences belong in the talk or the speaker notes (`\note{}`), not on the wall; keep bullets to one line.
- **A figure beats a bullet list; a bullet list beats a table.** Dense tables are for the paper — show the one row that matters.
- **One visual per slide, not a collage**, and it carries the slide's claim; no decorative stock images or clip art.
- **A number or figure on a slide comes from the same archived output as the paper's**, never redrawn or retyped by hand.
- **No slide-by-slide outline recaps** ("Where are we?"); the structure should be audible without them.
- **Every element is legible from the back row**: titles ≥ 32 pt, body ≥ 20 pt, no footnote-sized legends, no more than ~8 lines of content.
- **Text over a photograph sits on a dark band** (black, 40–50 % opacity); never rely on the image being dark enough.
- **One layout, declared once in the preamble**: same title position, fonts and sizes on every slide. Consistency beats originality.
- **Overlays reveal, they do not animate.** Use `\pause` to stage an argument, never for decoration.
- **Count against the slot**: about one slide per two to three minutes; a staged build counts once.
