---
name: user_paper_release_subdir_layout
description: Author's paper/deck filing model — one dir per paper moving between state folders, with an immutable append-only release/ subdir; editorial replies go in the release they judged
metadata:
  type: user
---

**One directory per paper.** The whole dir moves between state folders under
`~/CNRS/papiers/`: `actif/` (being worked on) ⇄ `sent/` (out for review) →
`published/`, round-tripping `actif ⇄ sent` across R&R rounds. `grenier/` is the
attic (abandoned/old); `reviews/` is unrelated (reviews done for others). Slide
decks follow an analogous, less formal `~/CNRS/missions/{actif,done}` taxonomy.
The paper keeps its identity as it moves — state is the parent folder, not a
rename.

**Inside the paper dir, `release/` is immutable and append-only** — one subdir
per submission, named `<YYYY-MM-DD> <description>/`
(e.g. `2026-07-07 Initial fulltext submission/`, `2025-01-14 extended abstract/`).
Each is a frozen snapshot of exactly what was submitted that round. (Legacy dirs
vary — some use `releases/` or bare `release-<date>-<venue>/`; the current
convention is `release/`.)

**Editorial decisions and referee reports are filed into the `release/` subdir of
the submission they judge** — retroactively, since the reply lands weeks or
months after the submission was sent. Store as tracked diffable text (extract
from the received PDF/email; the binary is transient). They belong beside the
immutable snapshot they evaluated — **not** with the mutable working copy at the
top of the paper dir, and **not** in a new folder of their own.

Recorded as a fact to apply with judgment, not a hard rule
([[feedback_dont_codify_hard_rules]]). Inferred from real practice on request
(IDH 0264 discussion, 2026-07-10). Related: [[feedback_rr_intake_is_laborious]].
