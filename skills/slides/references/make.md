# slides make

Source text in, beamer deck out; ODP only on request. Steps run in order,
sequentially: each consumes the previous one's decision.

1. **Message and slot.** State the central message in one sentence and the
   slot length; the slide budget follows from the doctrine's pace bullet. No
   message yet → `/message-framing`, then come back.
2. **Title plan, nothing else.** Write the slide titles as a numbered list.
   Apply the titles-alone test; cut every title that does not serve the
   message. In an interactive session this list is the one checkpoint the
   author signs off before any LaTeX is written — restructuring a title list
   is free, restructuring a built deck is not.
3. **One visual per title.** Map each slide to one figure, photograph or
   diagram, or to none. Figures come from the project's archived outputs
   (the files the paper's `\includegraphics` reads); photographs are the
   author's or properly licensed, ≥ 1920 px wide for a full-bleed slide.
   Convert WebP or AVIF to PNG or JPG before LaTeX sees them.
4. **Build.** `\documentclass[aspectratio=169]{beamer}` unless the venue
   says 4:3. Declare the layout once in the preamble (theme, fonts, title
   position); no per-frame styling. Speaker text goes in `\note{}`. For text
   over a photograph, draw the band with TikZ:
   `\fill[black,opacity=0.45]` in a `remember picture,overlay` picture.
   The build gates on its log like any manuscript (`rules/manuscript-build.md`).
5. **Render and look** (router § Render and look). Then run the review mode
   on the PDF (`references/review.md`) and fix its critical and important
   findings before handing over.
6. **ODP or PPTX, only when asked.** Convert the final PDF:
   `soffice --headless --infilter=impress_pdf_import --convert-to odp deck.pdf`
   (`pptx` likewise). It needs LibreOffice Impress and Draw installed; slides
   come back as positioned text and drawing objects, editable but not
   restyled. Render the converted file back to PDF and look again: a
   conversion is a new artifact.

Deliver the `.tex` source and the PDF; the PDF is the projection copy.
