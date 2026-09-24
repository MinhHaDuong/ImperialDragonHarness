---
name: feedback-zotero-everything-cited
description: "Every work cited in a manuscript goes into Zotero; fetch full texts with DOIfetch (~/CNRS/code/DOIfetch), legal sources only"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f9f37278-82b1-4adf-8dc4-82838f75664a
  modified: 2026-09-23T11:04:49.856Z
---

Add to Zotero every work cited in the manuscript, with its full text when it can be obtained. Stated
by Minh on 2026-09-23 while adding the EKC references to the Gavard & Schoch comment.

**Why:** Zotero is the system of record for sources (EDM discipline); a citation without a stored copy
cannot be checked later.

**How to apply:**
- When a reference enters the text, stage its PDF in `docs/` and import it to Zotero in the same
  session; dedupe first. A citation-only entry is acceptable when no full text is obtainable.
- To fetch full texts, use DOIfetch: `~/CNRS/code/DOIfetch`, `uv run fetch_istex.py --doi …`, or
  `fetch.py --source …`. ISTEX works via CNRS access and found Stern, Gerlagh & Burke 2017 (EDE) when
  Unpaywall had nothing. Use only its legal sources (crossref, unpaywall, hal, istex, ezproxy), never
  scihub or libgen.
- Authors' working-paper versions on institutional repositories are a fallback. The ANU DSpace API
  gave Stern 2017 when AgEcon Search blocked scripts.

Related: [[project-correction-process-with-authors]].
