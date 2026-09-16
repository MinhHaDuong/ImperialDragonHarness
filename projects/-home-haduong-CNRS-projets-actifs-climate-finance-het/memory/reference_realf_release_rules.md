---
name: realf-release-rules
description: "REALF book (minh.haduong.com/realf.html, How-tos 41/42/43/45/51) — the author's business rules for submitting, revising, and releasing research outputs"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7916be61-b5ab-4c43-9ab3-33af97f51055
  modified: 2026-07-29T14:16:31.133Z
---

*Research Excellence à la Française* (Ha-Duong 2025, PDF at
minh.haduong.com/files/HaDuong-2025-REALF.pdf) is the source of truth for
release/submission business rules. Verified against it 2026-07-29.

**How-to 41 (submit):** sleep on it; co-author approval; complete archive
(raw data, scripts, processed data, code, documentation) and REBUILD the
paper, figures, and tables from that package — "If you can't rebuild it,
don't release it"; tag the release in source control and package the files
on GitHub; archive data+code+results on Zenodo; save a read-only copy of
all submitted material; submission letter addresses the editor by name.

**How-to 43 (revise):** directory moves `papiers/sent` → `papiers/actif`
during revision, back to `sent` at resubmission. Deliverables: revised
manuscript, revised manuscript WITH CHANGES HIGHLIGHTED, detailed reply to
reviewers. You may reject a comment — convince the editor, not the
reviewer.

**How-to 42 (preprint):** author's preprint with French abstract and
keywords, archived on HAL; update the list of publications; embargo as
fallback if an editor objects.

**How-to 45 (Zenodo):** unambiguous standalone title; author = who did the
work; date = first release; methods description detailed enough to
reproduce in principle; per-file contents description; pick a community;
verify upload type, language, author, publication date.

**How-to 51 (homepage):** showcase 3–5 latest productions, static hosting,
valid HTML/CSS, no broken links, HTTPS, accessible.

**How to apply:** at every submission/resubmission, check the package
against 41/43 (the changes-highlighted manuscript is the most often
forgotten deliverable); at every deposit, 45; after every release, 42/51.
Related: [[project_release_needs_codedata_doi]].
