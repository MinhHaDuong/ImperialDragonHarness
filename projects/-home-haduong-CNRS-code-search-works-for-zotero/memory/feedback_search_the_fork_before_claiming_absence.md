---
name: feedback_search_the_fork_before_claiming_absence
description: "The implementation lives in the untracked fork/ checkout, so a repo-side grep returns nothing for code that exists; never report that as \"not built\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c34e2a1c-bfb3-41ee-9717-feaba5182542
  modified: 2026-09-03T09:50:56.611Z
---

The code lives in `fork/`, an untracked separate checkout, and often on a
branch that is not the one checked out there. `search-works-for-zotero` itself
holds spec, tickets and bench drivers — see
[[feedback_repo_prepares_upstream_it_ships_nothing]]. So a search of this
repository returns nothing for work that exists and ships, and the null reads
exactly like a real absence.

Twice in one session (2026-09-03) that null became a false claim, both caught
by the author, neither by me:

- **"seg/1 is not coded."** It was built the previous day — fork branch
  `t0028-seg1` at `f936102`, 26 tests, fork suite 1 153 passing, the 45 MB
  dictionary cut into 1 982 entries in 3,9 s. The branch is not among the local
  fork's refs; it was pushed to the author's fork remote.
- **"pdf.js needs vendoring" (ticket 0560).** `pdfjs-dist` had been a declared
  fork dependency throughout, and `extractPdfOutline` in
  `fork/src/features/fulltext/pdf-pages.ts` already did the whole ticket, dated
  a day *before* the tracker that asked for it was filed.

A compounding slip worth its own line: the first grep used
`--include="*.ts" --include="*.js" --include="*.py"` and so missed
`bench/seg1_run.mjs`. **This repo's bench code is `.mjs`.** An extension
allowlist is a silent filter — it produces the same empty output as a genuine
absence.

**Why:** this is [[feedback_probe_needs_discriminating_control]] in its
cheapest form. A search that cannot reach where the code lives has an "all
clear" indistinguishable from "I could not look", and the whole ticket ladder
0557 was specified against that null — three of its seven children were
further along than filed, one of them complete.

**How to apply:** before writing that something is not implemented, look in
`fork/src/`, in the fork's refs (`fork/.git/refs/heads`, read from the
filesystem — the worktree guard refuses `git -C` into the shared checkout), and
in `SYNC.md`, which records what shipped upstream and in which release. Grep
without an extension filter, or include `*.mjs`. The ticket's own log is often
the fastest answer of all: 0028's log carried the build report, the branch, the
SHA and the measurements the whole time.
