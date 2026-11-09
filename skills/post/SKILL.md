---
metadata:
  category: publication
name: post
description: "Walk one blog post or op-ed through a stage (draft, publish, archive): PDF, HAL, gates."
disable-model-invocation: false
user-invocable: true
argument-hint: "<post> <stage: draft|publish|archive> [dry-run]"
---

# Post — one blog post or op-ed, one stage, one checklist

A blog post or an op-ed (tribune) leaves debts in three places: the page that
carries it (the blog, the newspaper, the partner site), the open archive that
makes it citable, and the author's own registers (personal page, roadmap,
the blog's journal). Each stage's checklist names every one. Resolve the
post, read the local conventions, then load the stage's checklist and walk it.

## Local conventions come from the project's AGENTS.md

This skill holds the stages, the routing and the gates. Places, recipes and
local habits live in the `AGENTS.md` of the directory that holds the post:
for a blog post, the blog's own repository (where posts live, the PDF
template, the publishing recipe for the blog's platform, the open-archive
recipe, the journal and backlog files, the personal bibliography's path); for
an op-ed, the missions directory or the project it was born in (where the
roadmap is, how frozen outputs are filed). Read it first. Its recipes are
authoritative: this skill points at them and never restates them. If no such
file exists, ask the author for those places before writing anything, and
offer the answers as that file's content.

## Resolving the post

The `<post>` argument names a post by its folder name or a unique part of it
(date, slug, title words). Look in the blog's posts folder
(`billets/<AAAA-MM-JJ slug>/` or as the local `AGENTS.md` names it), then in
the mission or project folders for an op-ed. Read what the folder already
records (README, journal lines, a `release/` subfolder, deposit responses):
that says what is already done. Two matches or none: ask, never guess.

## Routing: what this skill does not do

- Framing and cutting the text: `/message-framing`, then `/cut-prose`.
- Finishing a PDF that leaves the machine: `/pdf-finish`.
- A manuscript event (submission, decision): `/paper`. A trip: `/mission`.
- Page entries and open-archive deposits: `/update-publist`, with its own
  gates and status table; never copy them here.

## Written once, used by every stage

- **Outward acts.** Invoking `/post` does not authorize an outward mutation
  (publish, deploy, deposit, mail, signature). Each checklist names its gates
  and who clicks.
- **Provenance.** A frozen artifact is the authentic one, fetched from its
  source (the live post, the editor's published page, the deposit response),
  never rebuilt. For an op-ed, keep the version sent and the version
  published. Frozen outputs go in a dated `release/<AAAA-MM-JJ>/` subfolder,
  each with its hash (one `sha256sum` line per file, or the hash in the
  release record).
- **Links land on the version.** Fetch every DOI or URL entering a register
  and confirm it lands on the intended version: a DOI can return 200 while
  resolving to the previous deposit.
- **Evidence before a step.** Each step first looks in the post's folder for
  its evidence (a file, a journal line, a register row). Found: report it
  done and move on. With `dry-run`, the stage changes nothing: it lists each
  step as done, with its evidence, or missing.
- **Author-only items are asked, not dropped.** Each checklist ends with them;
  the stage is done when each has an answer, "no" included.

## Stages

- draft (until the text is settled): `references/draft.md`
- publish (the text goes live): `references/publish.md`
- archive (companion PDF, open archive, registers): `references/archive.md`
