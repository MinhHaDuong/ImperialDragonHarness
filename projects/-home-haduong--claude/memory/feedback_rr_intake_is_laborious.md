---
name: rr-intake-is-laborious
description: Journal Revise-and-Resubmit intake (ingest editor decision + reviewer comments) has no harness skill, so it's done by hand and is laborious; don't re-search Gmail for moved files, archive comments to a known path, and verify remark↔ticket coverage once with a deterministic check, not 2-3× manually
metadata:
  type: feedback
---

A full day (2026-06-18, ~12 sessions on the Oeconomia — Climate finance
manuscript) went into R&R *intake* entirely by hand because no skill exists:
PDF extraction of the decision letter + reviewer comments, a **vain Gmail
search** (the files had already been moved into `release/`), counting "60
atomic comments" down to "56 remarks", creating ~10 thematic tickets, and
**verifying coverage two or three times manually** because there is no
remark↔ticket ledger. A track-changes PDF for the author to annotate was
requested and never delivered (no skill). Every existing review skill produces
reviews of *our* manuscript — the inverse of ingesting a journal's.

**Why:** R&R intake is a recurring, project-agnostic workflow (every journal
paper hits it) with a fixed shape — extract → archive → structure into remarks
→ map to tickets → verify coverage → render revisions for annotation. Done ad
hoc it burns turns on re-finding files and re-counting, and the
highest-value step (a marked-up PDF) gets abandoned mid-feasibility.

**How to apply:** when the author says "we got R&R comments" / "ingest the
decision letter", expect this friction and front-load the cheap fixes — (1)
don't hand-search Gmail: ask where the files were saved or check `release/`
first (journal artifacts get moved there); (2) archive the comments to one
documented path so the next session doesn't re-hunt; (3) build the remark↔ticket
coverage check once and trust it — re-counting by hand 2-3× is the tell that a
deterministic ledger is missing. The durable fix is the
`ingest-decision-letter` + `track-changes-pdf` skill chain, ticketed in IDH
0265. Author sweep request, 2026-06-18.
Related: [[feedback_skills_just_work_no_config_blocks]], [[feedback_harness_is_the_deliverable]].
