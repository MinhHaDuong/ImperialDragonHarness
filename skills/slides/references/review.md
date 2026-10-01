# slides review

Diagnose an existing deck and return fixes ranked by what they cost the
talk. Read-only: change the deck only when asked.

1. **Inventory.** Render (router § Render and look); `pdfinfo` for the page
   count. Ask the slot length and the intended message if they are not
   given. List each slide: number, title, kind of visual.
2. **Diagnose**, against `rules/doctype/slides.md`, every bullet a check,
   in this order — narrative first, because a restructure voids the rest:
   - *narrative*: message statable from the titles alone; order; count
     against the slot;
   - *visual*: one idea and one visual per slide, the visual carrying the
     claim, one layout throughout;
   - *legibility*: sizes, contrast on photographs, pixelated or stretched
     images;
   - *fidelity*: every number on a slide matches the paper or pipeline
     output it claims; a mismatch is critical.
   No message recoverable from the titles → stop the diagnosis there and
   send the author to `/message-framing`; visual notes on a deck about to
   be restructured are wasted.
3. **Rank.** *Critical* — blocks understanding: no message, illegible text,
   a wrong number. *Important* — the audience will notice: layout drift,
   bullet walls, decorative images. *Polish* — sharper wording, spacing.
   Separate what the doctrine requires from taste, and defer on taste.
4. **Report.** Critical first; per issue: slides affected, the problem, the
   concrete fix. Give polish only when nothing above it remains or when
   asked. A strong deck gets a one-line verdict, not a manufactured list.

When the deck is ours in beamer and the author wants the fixes applied,
switch to `references/make.md` from step 4, then review again.
