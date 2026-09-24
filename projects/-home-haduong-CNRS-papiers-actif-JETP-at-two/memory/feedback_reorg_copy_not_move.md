---
name: feedback_reorg_copy_not_move
description: "When reorganizing/relocating a research directory, use cp not mv, and check sibling-project conventions before inventing a structure"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d0150b9b-532b-4fc4-854e-67338ee51348
  modified: 2026-09-10T16:11:37.443Z
---

When asked to relocate and reorganize a research/project directory, use
`cp -r` (or equivalent), never `mv`, even when the instruction sounds like a
plain move ("on le déplace"). Corrected 2026-09-10 (JETP reorg): I moved
`~/CNRS/papiers/actif/JETP at two/` to `~/CNRS/projets/actifs/jetp/` with
`mv`, then the user said "Juste copier... je supprimerai moi-même" — they
wanted to verify the new location before the old one disappeared, and to
control deletion themselves.

**Why:** the user treats deletion of their own research material as a
decision they make deliberately, not a side effect of a reorg. A `mv` also
forecloses an easy do-over if the target structure turns out wrong — which
is exactly what happened next (see [[project_deux_papiers_jetp_2026-09-08]]:
the ad hoc "one folder per paper" structure I invented was itself wrong).

**How to apply:** for any file-system reorg of the user's own research/paper
directories (not code in a git repo, not scratch/temp files), default to
copy-and-verify, and let the user do the final deletion of the source once
they've confirmed the new layout — unless they explicitly say "move" *and*
have already told you it's fine to delete the source.

**Second half of the same correction — don't invent a structure cold.**
Before proposing subfolders for a reorganized project, look at how the
user's *other* active projects (`~/CNRS/projets/actifs/*`) are actually
organized. They are not "one folder per paper" — e.g. `climate-finance-het`
organizes by function (`deliverables/<doc>/` holds only the per-document
Quarto file; `data/`, `scripts/`, `config/` are shared once across every
deliverable). Check for this pattern, and check whether the new project
should merge into an existing one with overlapping infrastructure (same
data source, same measurement method) before scaffolding a new standalone
directory — ask the question explicitly rather than assuming independence.
