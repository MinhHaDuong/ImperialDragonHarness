---
name: includes-citation-guard-0244
description: "tests/test_cited_works_available.py now covers deliverables/_shared/_includes/**/*.md, not just top-level .qmd files"
metadata: 
  node_type: memory
  type: project
  originSessionId: c35c7aa1-5594-4c66-9bba-fb21050c17b7
---

`tests/test_cited_works_available.py`'s `QMD_GLOBS` was extended (ticket 0244,
PR #1048) to also scan `deliverables/_shared/_includes/**/*.md`. Previously it
only scanned `deliverables/*/*.qmd`, so citations inside AI-generated includes
were invisible to the fulltext-availability guard — exactly where the
ticket-0152 phantom citation ("Baran et al. 2024") had hidden.

Extending coverage immediately surfaced 3 real (non-fabricated) gaps in
`deliverables/_shared/_includes/zoo/`: `freeman1977set`, `kessler1963bibliographic`,
`min2021measuring`. All three resolved with local fulltext (Kessler via ISTEX,
Freeman + Min via the author's manual pull — see
[[feedback_user_pulls_land_in_downloads]]).

Ticket 0244 closed with the citation/provenance verification of the 4 includes
done, but author review (whether to downgrade the "AI-generated, not
human-reviewed" markers) deliberately **deferred, not waived** — markers stay
in place as a resume-flag for when techrep work restarts. Also logged in that
ticket for future attention: `changepoint-analysis.md` argues 2012 (not 2015)
is the better data-driven break-point, in tension with the
corroboration-not-causation framing in `writing.md` — [[feedback_oversell_breaks]].
None of the five includes is wired into a rendered `.qmd` yet, so nothing is
currently exposed to readers.
