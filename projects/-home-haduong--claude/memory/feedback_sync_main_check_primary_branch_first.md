---
name: sync-main-check-primary-branch-first
description: Primary checkout may sit on a feature branch — "sync local main" via merge --ff-only advances THAT branch; update main by ref (fetch origin main:main) and preserve dirty overlapping files across the sync
metadata:
  type: feedback
---

"Sync local main" on the primary checkout (`git -C ~/.claude merge --ff-only
origin/main`) silently fast-forwards **whatever branch is checked out there** —
on 2026-07-11 that was another session's `monster-ticket-reflex`, not main
(harmless only because its PR #473 had already merged). Two companion traps in
the same operation: (a) the checkout can carry another session's uncommitted
memory write (index lines + `!!`-ignored entry files, see
[[idh-gitignore-whitelist-add-f]]) that collides with an incoming merge touching
the same file; (b) plain `git branch -f main origin/main` is unsafe if main is
checked out elsewhere.

**Why:** the primary checkout is shared state across sessions; assuming it is
on main turns a routine sync into a mutation of someone else's branch or a
clobber of their in-flight write.

**How to apply:** don't run the raw idiom by hand — run `scripts/sync-local-main.sh
[checkout]`. It moves only the default branch (never whatever branch is checked
out), fast-forwards where main lives, refuses a diverged or dirty target, leaves
local state untouched, and exits 0 (hook-safe). If a dirty file overlaps the
incoming diff the script reports it and moves nothing: back the file up, `git
checkout -- <file>`, re-run, then re-apply only the dirty lines on top — never
discard, never bare stash (stash stack is shared, see rules/git.md).

Promoted to rules/git.md § "Local main syncs eagerly" with mechanism
`scripts/sync-local-main.sh` (session-start hook + /merge post-step), ticket
0276, 2026-07-11 — the rule and script are now authoritative; this entry
records the originating incident.
