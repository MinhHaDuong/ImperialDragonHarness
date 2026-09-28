---
name: feedback-privacy-session-2026-09-28
description: "Lessons from the 2026-09-28 privacy session: concurrent-session branch races, absolute hooksPath blindfolding worktree commits, and gitignore-whitelist precedence over .git/info/exclude"
metadata:
  node_type: memory
  type: feedback
---

Three durable lessons from the 2026-09-28 personal-data session (PRs #1039, #1044; the email skill that became private).

**Concurrent sessions race the shared checkout when you branch from HEAD.**
A `git checkout -b` cut from the primary checkout can pick up another
session's just-committed WIP as ancestry: this session's first branch grew from
`tickets/albert-activation`'s tip, committed one second earlier, and its first
push carried that ticket's commit (reflog
`moving from tickets/albert-activation to email-skill-20260928`). Branch from
`origin/main` explicitly (`git worktree add -b <name> origin/main`), and do
multi-step PR work in a throwaway worktree so the shared checkout's HEAD is
never an input.

**core.hooksPath is absolute, so worktree commits are validated by the PRIMARY
checkout's hook file, not the branch's.** A pre-commit guard added on a branch
does not fire for that branch's own commits until the branch is checked out in
the primary checkout — a worktree commit that "passed" the guard proves
nothing. CI is the authoritative gate pre-merge; say so in the PR body
(precedent: the personal-data-guard shipped in #1039 and caught its own
regression only in pytest-guard, #1044).

**A repo whitelist `.gitignore` beats `.git/info/exclude`.** This repo ignores
everything (`*`) then re-includes harness components (`!skills/**`); a
`.git/info/exclude` entry cannot override a later `.gitignore` negation
(same-dir .gitignore has higher precedence). To keep private symlinks (e.g.
`skills/email` → the private overlay) out of the tree, the exclusion must live
in the repo's `.gitignore` itself. Also: exclude patterns with a trailing
slash never match symlinks.

**Why:** each of these produced a silent wrong result (a polluted push, a green
pre-commit that hadn't run, an untracked symlink that looked excluded).
**How to apply:** branch from origin/main in a worktree; treat worktree
pre-commit passes as informational; check `git check-ignore -v` before
trusting any exclude for a symlink.
