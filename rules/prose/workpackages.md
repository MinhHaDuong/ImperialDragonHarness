---
paths:
  - "**/*.tex"
  - "**/*.qmd"
  - "**/docs/**"
last-reviewed: 2026-10-06
---
# Paper-repo workpackages

Moved out of the resident `git.md` (2026-10-06, ticket 1059): these rules
apply only inside manuscript/report repos, so they load on prose-file touch
instead of every session.

- **Don't gitignore handoff artifacts.** Generated files a downstream workpackage consumes (figures, tables, `\input` macros) are durable — commit them; caches, aux files and the final PDF are regenerable — gitignore. Sources and bibliography staging: [../zotero.md](../zotero.md), Zotero is their system of record.
- **Prose workpackages are edited in place; the author edits only in their own checkout.** In paper repos, worktree + branch + PR covers code and data; manuscript prose is co-edited in short interactive turns in the author's checkout, committed at session end or milestones, reviewed as the PDF and `latexdiff` between tags. Autonomous prose passes produce *reports*; an autonomous manuscript change goes through a PR, never concurrently with interactive editing of that file. Agents carry the sync, never the author: pull before editing a file the author may have touched; agent work reaches them only through `main` (`scripts/sync-local-main.sh`); show unmerged work as a diff, a build or a PR link, never "open the worktree". The harness repo keeps its no-exceptions gate.
- **Name workpackage directories in plain language** (`marches-carbone/`, not `p1/`); program codes stay in tickets.
