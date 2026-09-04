---
name: feedback-check-ticket-status-against-main
description: "A session that starts on a stale/diverged branch can read a ticket as open when it is already closed on main — check origin/main before investigating an \"open\" ticket"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 43e58a38-2000-40f7-9ca5-53c07d2b98f9
  modified: 2026-09-01T13:24:36.604Z
---

Before investing real work on a ticket that looks open, confirm its status
against `origin/main`, not against whatever branch the session's primary
checkout happens to be sitting on.

**Why:** on 2026-09-01 a session's system-reminder context was built from
the primary checkout on branch `t0091-pr2-expansion` — significantly behind
`main` (missing at least five merged PRs). Ticket 0504 read as open there
and the session spent real effort exploring the upstream fork's commit
history before entering a fresh worktree (branched from `origin/main` per
[[project_registry_not_knobs]]-adjacent EnterWorktree defaults) and
discovering 0504 was already closed — autoclosed via PR #128, with its own
successor tickets (0505, 0506, 0520) already filed and waiting. The
work was not wasted (0505/0506/0520 needed the same investigation), but the
premise ("is 0504 still open") was answered wrong for a while, and a
differently-shaped ticket could have led to real duplicate work.

**How to apply:** when a ticket's state matters to the plan (not just
skimming), `find`/`cat` it from a worktree freshly branched off
`origin/main` (or `git show origin/main:path` from wherever you are)
before treating "open" as current. This is the same discipline
`rules/workflow.md` § Sync before starting work already states for code —
apply it to ticket/document state reads too, not only to "would my edit
collide with parallel work."
