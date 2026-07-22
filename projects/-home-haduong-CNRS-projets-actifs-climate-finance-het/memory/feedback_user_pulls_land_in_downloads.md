---
name: user-pulls-land-in-downloads
description: "When the user manually fetches a PDF (click-and-read), it lands in ~/Downloads/, not docs/articles/"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c35c7aa1-5594-4c66-9bba-fb21050c17b7
---

When the user says they pulled a paper themselves (manual browser download,
institutional access, etc.), the PDF lands in `~/Downloads/`, not the
project's `docs/articles/` staging directory.

**Why:** The user's own fetch flow always drops files there — stated
explicitly 2026-07-15 after manually pulling `freeman1977set` and
`min2021measuring` (Sci-Hub/Anna's Archive was network-blocked from the
agent's sandbox; user fetched via browser instead).

**How to apply:** After the user says "I pulled/got/downloaded X myself",
check `~/Downloads/` (sort by `ls -lat`) for a plausible match before asking
where the file is. Verify content with `pdftotext` against the bib entry's
title/authors before staging — filenames in Downloads are not reliable (may
be a DOI hash, Anna's Archive naming, etc.). Then copy into the *worktree's*
`docs/articles/<bibkey>.pdf` (not the primary checkout — see
`feedback_worktree_local_hook_commit`-style path discipline) and add the
`file=` field to the matching `main.bib` entry.

See also [[project_doifetch_sync]] for the separate external-tool sync path
(when *the agent* fetches via DOIfetch, not the user).
