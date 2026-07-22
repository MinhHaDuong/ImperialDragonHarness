---
name: show-rendered-page-for-visuals
description: "Before asking the user's opinion on a visual/CSS change, render and open the page — don't just describe the diff"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b21a547b-b2f9-43c0-affd-80e10ab82651
---

When a change affects visuals (CSS, layout, typography, colors), build/render the
page and open it in the browser before asking the user what they think. Don't
settle for describing the diff in prose.

**Why:** The user judges visuals by looking, not by reading CSS. A described
change ("dashed, 40%-alpha underline") can't be evaluated without seeing it on
the actual busy layout it has to coexist with.

**How to apply:** After a visual edit, run the project build (see `Makefile` /
`index.py`) to produce the rendered HTML, then open it (e.g. `xdg-open` the
output file, or a screenshot) and point the user at it — *then* ask for the call
on alpha/style/dial.

**Build it faithfully or you will misread the page.** In a worktree, `../files`
and `../images` are absent, so `bib2htm` silently downgrades every PDF-backed
title from `<a class="title">` to a plain `<span>` — the page renders *without
its title links*, which once led me to wrongly tell the user "titles aren't
links." Symlink the assets before building (`ln -sfn
/home/haduong/CNRS/html/files /home/haduong/CNRS/html/src/.claude/worktrees/files`).
See `html/src/AGENTS.md` § "Worktrees: untracked assets live above the repo
root" — read it before any preview build.
