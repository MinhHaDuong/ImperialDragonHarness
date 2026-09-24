---
name: project_cadens_realf_split
description: "cadens (research pipeline, git) and realf.hypotheses.org (the author's blog, no git) are separate projects; cadens's own blog plan was retired 2026-09-15 in favor of realf's backlog"
metadata: 
  node_type: memory
  type: project
  originSessionId: 205d21b8-033a-430e-bad8-23da7bf7a8f0
  modified: 2026-09-15T15:12:06.428Z
---

cadens (`~/CNRS/projets/actifs/cadens/`) is a git-tracked data/research
pipeline (harvest, analysis, paper, tickets via `erg`). realf.hypotheses.org
(`~/CNRS/projets/actifs/realf.hypotheses.org/`) is the author's general
research blog — not a git repo, plain Markdown files (`backlog.md`,
`journal.md`, `projet-editorial.md`, `strategie-editoriale.md`) — covering
several arcs (the AI harness, ASEAN/France energy transition, climate
finance, history of economic thought, IAM), of which cadens is one topic.

**Why:** cadens's STATE.md originally assumed cadens itself would become the
Hypotheses.org blog ("pivot from single paper to blog series") and had its
own 17-post `blog/calendar.md` + `blog/framing-note.md`. When realf actually
opened, it turned out broader, already had one published post, and named
cadens as a single one-line backlog placeholder with a different angle
(psychological risk / prosthesis-orthosis) than cadens's own empirical
framing. Decided 2026-09-15 (cadens ticket 0040, PR #47): keep the two
projects separate (different tooling — git+tickets vs plain files; different
scope — one topic vs the author's whole blog), but retire cadens's standalone
blog plan and fold its still-useful post ideas into realf's own backlog at
realf's pace, after reviewing every post rather than declaring the whole plan
superseded in bulk.

**How to apply:** future blog-editorial work for cadens content happens in
realf's `backlog.md`/`journal.md`, not in cadens's `blog/`. Cadens's own
`blog/framing-note.md` and `blog/calendar.md` still exist with a superseded
banner, kept as historical record — don't revive them as a live plan without
re-checking with the author first.
