---
metadata:
  category: publication
name: paper
description: "Run a manuscript lifecycle event (submitted, decision-received, resubmitted, accepted, published): register choice, files, outward gates. Not for venue choice (/choose-venue)."
disable-model-invocation: false
user-invocable: true
argument-hint: "<paper> <event: submitted|decision-received|resubmitted|accepted|published>"
---

# Paper — one manuscript event, one checklist

A manuscript's life starts at submission; choosing the venue belongs to
`/choose-venue` and `/conference-submission-prep`. At each event the repo side
(STATE, tickets, tag, submission branch) is half the bookkeeping: two registers
outside git and the frozen-output folder go stale unless this session updates
them. Read the local conventions, answer the register question, then load the
stage's checklist and walk it.

## Local conventions come from the papers directory

This skill holds the stages, the routing and the gates. Places and local
habits live in the `AGENTS.md` of the papers directory, the one holding a
folder per manuscript (walk up from the manuscript's folder to find it). Read
it first: it names where each register lives and how it is updated, the folder
states a manuscript moves through, how dated event subfolders are named, and
the author's preferences. If no such file exists, ask the author for those
places before writing anything, and offer the answers as that file's content.

## Which register: one, the other, never automatically both

- The **roadmap** tracks *work in progress*. Nearly every event belongs there,
  even one that produces nothing citable.
- The **publications list** tracks *works*. An entry announces something that
  exists: a proposal under consideration is not one. Create the entry when the
  piece is accepted or the contract signed.

Worked example: two book-proposal dossiers went to publishers. The roadmap row
moved from "dossiers ready" to "sent on 9 September 2026"; the publications
list stayed untouched, since announcing a book that may never be contracted
creates a public debt repaid later in silence. Write the answer in the commit
message or event record; a decision left implicit is retaken from scratch next
time.

## Written once, used by every stage

- **Outward acts.** Invoking `/paper` does not authorize an outward mutation
  (deploy, deposit, mail). Each checklist names its gates and who clicks.
- **`/update-publist`** owns the page entry, the HAL deposit and the entry
  types (per `/update-publist`'s status table; never copy it here). Load it and
  follow its gates; if the runtime refuses the load, ask the author to type it.
- **Provenance.** A frozen artifact is the authentic one, fetched from its
  source (mail archive, publisher, HAL, the homepage's hosted file), never
  rebuilt from the repo. Write one `sha256sum` line beside the frozen copy.
- **Two folder conventions, never merged.** The paper repo's `release/<date>/`
  holds tracked text (letters, reviews, responses). The manuscript's folder in
  the papers directory holds frozen authentic outputs only, one dated
  subfolder per event, no editable source; the folder changes state with the
  paper as the local `AGENTS.md` says.
- **Links land on the version.** Fetch every DOI or URL entering a register and
  confirm it lands on the intended version: a DOI can return 200 while
  resolving to the previous deposit.

## Stages

- submitted: `references/submitted.md`
- decision-received (accept, revise or reject): `references/decision-received.md`
- resubmitted: `references/resubmitted.md`
- accepted: `references/accepted.md`
- published: `references/published.md`
