---
name: submission-event
description: "Classify a manuscript submission event — submitted, resubmitted, accepted, published — by which external register its object belongs in, then propagate it to the homepage publications list and/or the CNRS secretariat roadmap. The roadmap tracks work in progress; the publications list tracks works, so never update both automatically."
disable-model-invocation: false
user-invocable: true
argument-hint: "<paper> <event: submitted|resubmitted|accepted|published>"
---

# Submission events — propagate to the external registers

Was `rules/submission-events.md`, resident in every session until 2026-09-09;
its trigger is a task, not a file, so it is a skill (ticket 0572).

When a manuscript's submission state changes, the repo side — STATE, tickets,
tags, submission branch — is not the whole bookkeeping. Two registers live
outside git and go stale unless the relevant one is updated in the same
session. Consider both as part of the wrap-up; they are author-visible
deliverables, not chores to defer (author directive, 2026-07-29, after a
revision-1 resubmission where both had to be asked for after the fact).

## Which register — and/or, never automatically both

The two registers record different objects, so an event can belong to one and
not the other:

- The **roadmap** tracks *work in progress*. Nearly every submission event
  belongs there, including one that produces nothing citable.
- The **publications list** tracks *works*. An entry announces something that
  exists. A proposal still under consideration is not a work: create its entry
  when a contract is signed or the piece is accepted, not when the envelope
  leaves.

Worked example (2026-09-09): two book-proposal dossiers went to publishers.
The roadmap row moved from "dossiers prêts" to "envoyés le 9 septembre 2026";
`Ha-Duong.bib` was deliberately left alone. Announcing a book that may never be
contracted creates a public debt that is later repaid in silence.

Ask "which register does this event's object belong in?" and write the answer
in the commit message or event record. A decision left implicit is retaken from
scratch at the next event, and the two readings do not converge.

## 1. Homepage publications list

`~/CNRS/html/src/Ha-Duong.bib`: when this event belongs in the publications
list, the explicit-only `/update-publist` skill owns the entry-type mapping,
build, verification and deploy procedure. If the author has not already
authorized this publication-list update, ask them to invoke `/update-publist`
(usually with `--page-only` when no deposit is due). If the current session
already carries explicit authorization for the update, read and follow that
procedure. Invoking `/submission-event` alone is not authorization for the
outward mutation or deployment.

## 2. CNRS secretariat roadmap

`~/CNRS/secretariat/Feuille de route <year>.odt`: update the paper's row — état
accompli, prochaine action — in the style of the neighbouring rows, then
regenerate the companion PDF with a headless converter. This register holds
manuscripts only.

## The check that is not optional

**Verify every link you write on its landing page, not on its status code.**
Fetch each DOI or URL entering a register and confirm it lands on the intended
*version*: a DOI can return 200 while resolving to the previous deposit. One
revision-1 homepage shipped a link to v1.1 and needed a hotfix (2026-07-29).
