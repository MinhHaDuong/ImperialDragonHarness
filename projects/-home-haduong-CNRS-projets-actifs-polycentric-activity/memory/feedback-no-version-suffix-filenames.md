---
name: feedback-no-version-suffix-filenames
description: "Never create version-suffixed artifact names (-round3, -revision, -new); one canonical manuscrit.pdf, git holds history"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f10ac93f-e26c-4c6e-91eb-08c84ce03ec3
  modified: 2026-08-12T05:42:00.236Z
---

Author directive (2026-08-12): no filename suffixes like `-roundN`, `-revision`,
`-new`, `-propre` on manuscripts or their PDFs. One canonical `manuscrit.tex` /
`manuscrit.pdf` per workpackage.

**Why:** With suffixed copies the author must guess which file is current;
git already provides the version history (tags, latexdiff between refs).

**How to apply:** Overwrite the canonical file and commit; use git tags for
frozen submission states; render variants via transform scripts, never by
saving a renamed copy.
