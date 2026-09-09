---
name: submission-event
description: "Propagate a manuscript submission event — submitted, resubmitted, accepted, published — to the two registers that live outside git: the homepage publications list and the CNRS secretariat roadmap. Both go silently stale otherwise, and both are author-visible deliverables rather than chores to defer."
disable-model-invocation: false
user-invocable: true
argument-hint: "<paper> <event: submitted|resubmitted|accepted|published>"
---

# Submission events — propagate to the external registers

Was `rules/submission-events.md`, resident in every session until 2026-09-09;
its trigger is a task, not a file, so it is a skill (ticket 0572).

When a manuscript's submission state changes, the repo side — STATE, tickets,
tags, submission branch — is not the whole bookkeeping. Two registers live
outside git and go stale unless updated in the same session. Propose both as
part of the wrap-up; they are author-visible deliverables, not chores to defer
(author directive, 2026-07-29, after a revision-1 resubmission where both had
to be asked for after the fact).

## 1. Homepage publications list

`~/CNRS/html/src/Ha-Duong.bib`: update the entry — title, date, status note in
the `type` field, DOI (the *concept* DOI for datasets) — then rebuild and
deploy. `/update-publist` owns this register in detail, including the entry-type
mapping and the deploy step; call it rather than editing by hand, and use its
`--page-only` flag when the event does not warrant a deposit.

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
