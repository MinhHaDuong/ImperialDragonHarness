---
name: feedback-odt-fixed-row-height-clips
description: ODT/LibreOffice tables with fixed row heights silently hide overflowing text; after editing, verify the rendered text against the source for every cell
metadata:
  type: feedback
---

LibreOffice table rows styled with a fixed `style:row-height` clip whatever does not fit. The text
is still in `content.xml` but invisible on screen and in PDF, with no warning. On 2026-09-23, rows
added to `~/CNRS/secretariat/Feuille de route 2026.odt` were clipped, and the check at the time
missed it. A later sweep found seven older cells of Minh's own roadmap already hidden that way,
for example the note that the Oeconomia paper was rejected with "resoumission interdite".
Fix: replace `row-height` with `min-row-height` plus `use-optimal-row-height="true"`. All 21 row
styles of that file were converted.

**Why:** a check of the XML, or of the first lines of the render, passes while text is hidden. Only
comparing the source against the rendered text catches it.

**How to apply:** after any ODT table edit, render headless in a separate profile
(`soffice -env:UserInstallation=file:///tmp/... --convert-to pdf`, so an open LibreOffice window is
not disturbed). Then check that each cell's closing words appear in the `pdftotext -layout` output.
A hit split across a line break is a false alarm; check it in context.
