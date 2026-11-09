---
metadata:
  category: publication
name: mission
description: "Walk one stage of a work trip (prepare, check, return): dossier, receipts, report, gates."
disable-model-invocation: false
user-invocable: true
argument-hint: "<dossier> <stage: prepare|check|return>"
---

# Mission — one trip, one stage, one checklist

A work trip leaves debts in three places: the employer (travel order, expense
claim, receipts, activity report), the lab (a short report to colleagues) and
the author's own registers (personal page, open archive, roadmap). Nothing
else in the harness tracks them, so each stage's checklist names every one.
Resolve the dossier, read the local conventions, then load the stage's
checklist and walk it.

## Local conventions come from the missions directory

This skill holds the stages, the routing and the gates. Places and local
habits live in the `AGENTS.md` of the missions directory, the one holding a
folder per trip: how active and closed dossiers are named, the rubriques a
closed dossier is filed under, where the institution's forms and booking
procedures live, which tools read the closed dossiers (and the paths they
read), where the roadmap is, and the author's preferences. Read it first. If
no such file exists, ask the author for those places before writing anything,
and offer the answers as that file's content.

## Resolving the dossier

The `<dossier>` argument names a trip by its folder name or a unique part of
it (date, event). Look under the active dossiers first, then under the closed
ones: a closed dossier is renamed on the move, so match the date and the event
rather than the whole name. Read its README if one exists: a table of
subfolders and a closing section record what is already done. Two matches or
none: ask, never guess.

## Routing: what this skill does not do

- Choosing the venue: `/choose-venue`. Writing the abstract:
  `/conference-submission-prep`.
- The talk itself: `/message-framing`, then `/slides`.
- A manuscript event met during the trip (submission, decision):
  `/paper`.
- Page entries and open-archive deposits: `/update-publist`, with its own
  gates and status table; never copy them here.

## Written once, used by every stage

- **Outward acts.** Invoking `/mission` does not authorize an outward mutation
  (booking, payment, mail, deploy, deposit, signature). Each checklist names
  its gates and who clicks.
- **Provenance.** A frozen artifact is the authentic one, fetched from its
  source (mail archive, booking site, the organisers' page), never rebuilt.
  Frozen outputs go in a dated release subfolder of the dossier, as the local
  `AGENTS.md` names it, with one `sha256sum` line per file.
- **Evidence before a step.** Each step first looks in the dossier for its
  evidence (a file, a README line, a register row). Found: report it done and
  move on. A dry run stops there and lists what is missing.
- **Author-only items are asked, not dropped.** Each checklist ends with them;
  the stage is done when each has an answer, "no" included.

## Stages

- prepare (before leaving): `references/prepare.md`
- check (the days before the talk): `references/check.md`
- return (after the trip, until the dossier is closed): `references/return.md`
