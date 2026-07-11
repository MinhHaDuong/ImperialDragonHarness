---
name: project-git-erg-scaffold
description: "P1 project repo root is polycentric_activity/ (renamed from 'Polycentric activity/' 2026-07-03), with conception/ and docs/ as gitignored scratch subdirs"
metadata: 
  node_type: memory
  type: project
  originSessionId: c78fd596-fa14-41fe-9ec6-22cd1f4fd694
---

As of 2026-07-03, the P1 project (*Local-to-Global No-Arbitrage on Production
Networks*) lives at `/home/haduong/CNRS/papiers/actif/polycentric_activity/`
— a real local git repository with a `tickets/` erg store (`tickets/erg`
binary, `.ergrc`, `AGENTS.md`) and a LaTeX paper-writing chain (`main.tex`,
`refs.bib`, `Makefile`, tectonic build). No remote is configured —
everything is local-only, so merges land on `main` directly with no PR step
possible.

History, for context: the repo was first bootstrapped with `.git` accidentally
nested one level down at `conception/` (root should have been the parent).
Ticket 0003 flagged the resulting dead `.gitignore` patterns (`docs/`,
`conception/` — meaningful only if the parent were root); it was resolved and
closed same-day by relocating `.git` up to the parent, which was then renamed
from `Polycentric activity/` (space, mixed case) to `polycentric_activity/`.
`docs/` (PDF reference library) and `conception/` (exploratory notes,
`note-idee-prix-polycentriques-*.md`, `p1-brique-*.tex`) are now correctly
gitignored scratch subdirectories at the true root; `main.tex` does not
`\input`/`\include` anything from `conception/`, so nothing in the tracked
build depends on ignored content.

**Surprising**: the session-start environment banner can report "Is a git
repository: false" — true only at the start of a scaffolding effort, stale
the moment a concurrent session initializes or relocates the repo mid-job.
Don't trust that banner at face value mid-session; re-check with `git
rev-parse --show-toplevel`.

**How to apply**: this project's directory name changed (2026-07-03) from
`Polycentric activity/conception` to `polycentric_activity` at repo root —
a session whose project-memory folder is keyed to the old path slug won't
automatically see these notes from a session rooted at the new path; treat
this file as historical if a future session can't find it. Multiple
concurrent sessions/worktrees are common in this project (seen 2026-07-03: a
bib-warning fix, a librarian bibliography pass, and the repo relocation
itself all landed on `main` mid-session from other work) — sync with `git
log` before assuming `main` is where you last left it, per
[[workflow-sync-before-work]].
