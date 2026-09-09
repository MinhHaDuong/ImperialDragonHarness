<!-- last-reviewed: 2026-09-09 -->
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

Propose them as part of the submission-event wrap-up; they are author-visible
deliverables, not chores to defer. (Author directive, 2026-07-29, at the
RDJ-26561 revision-1 resubmission — the homepage and roadmap updates had to
be asked for after the fact.)

## Which register — and/or, never automatically both

The two are not a pair to update in lockstep. They record different objects,
so an event can be due to one and not the other:

- The **roadmap** tracks *work in progress*. Nearly every submission event
  belongs there, including one that produces nothing citable.
- The **publications list** tracks *works*. An entry announces something that
  exists. A proposal still under consideration is not a work: its entry is
  created when a contract is signed or the piece is accepted, not when the
  envelope leaves.

Worked example (2026-09-09): two book-proposal dossiers went to publishers.
The roadmap row moved from "dossiers prêts" to "envoyés le 9 septembre 2026",
its next step becoming the follow-up date. `Ha-Duong.bib` was deliberately
left alone — announcing a book that may never be contracted is a debt repaid
in silence. Applied literally, the instruction above would have created that
entry.

So the wrap-up question is not "did I update both?" but "which register does
this event's object belong in?" Write the answer down, in the commit message
or the event record: a decision left implicit is retaken from scratch at the
next event, and the two readings do not converge.

**Check every link you write, on the landing page, not the status code.**
`curl -sIL` each DOI/URL entering a register and confirm it lands on the
intended *version* — a DOI can return 200 while resolving to the previous
deposit (the revision-1 homepage shipped a link to v1.1 and needed a hotfix,
2026-07-29).
