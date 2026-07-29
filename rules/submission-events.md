<!-- last-reviewed: 2026-07-29 -->
# Submission events — propagate to the external registers

When a manuscript's submission state changes — initial submission, revision
resubmitted, accepted, published — the repo side (STATE, tickets, tags,
submission branch) is not the whole bookkeeping. Two registers live outside
git and go silently stale unless updated in the same session:

1. **Homepage publications list** — `~/CNRS/html/Ha-Duong.bib`: update the
   entry (title, date, status note in `type`, DOI — concept DOI for
   datasets), rebuild (`make` in `~/CNRS/html/src/`), deploy
   (`make sync` in `~/CNRS/html/`, which validates first).
2. **CNRS secretariat roadmap** — `~/CNRS/secretariat/Feuille de route
   <year>.odt`: update the paper's row (état accompli, prochaine action) in
   the style of the neighbouring rows, then regenerate the companion PDF
   (`libreoffice --headless --convert-to pdf`).

Propose both as part of the submission-event wrap-up; they are author-visible
deliverables, not chores to defer. (Author directive, 2026-07-29, at the
RDJ-26561 revision-1 resubmission — the homepage and roadmap updates had to
be asked for after the fact.)
