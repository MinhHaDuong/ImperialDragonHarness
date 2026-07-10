---
name: feedback_stale_worktree_make
description: "After merging from a worktree, the session stays bound to it; builds run stale code — run make from the main checkout"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f849de87-bf31-4f36-8b5a-95ec3296ace4
---

When a session opens several PRs and merges them, its shell cwd can stay bound to
an early throwaway worktree whose branch was cut *before* those merges. Every
Bash command then resets into that stale tree, so `make <target>` runs the
**old** Makefile — a target added in a just-merged PR is "No rule to make target".

Concrete bite (2026-06-28): after merging the `make gide` recipe (#835), the user
ran `make gide` and got `No rule to make target 'gide'` — the session was parked
in `explore-conf-intro-heading` (branch `fix-substrate-smoke-numbering`, cut
before #833/#835), whose `manuscript.mk` lacked the target. The recipe was on
`main` the whole time.

**Why:** `ExitWorktree` no-ops here (the harness doesn't track this as an
EnterWorktree session), so the session can't be moved back to the primary
checkout mid-session; the cwd reset to the worktree is sticky.

**How to apply:** After merging work, run builds/commands against the **main
checkout**, not the session worktree: `make -C <primary-repo> <target>` or
`cd <primary-repo> && make …`. Before telling the user a freshly-merged target
"works", verify it from the primary checkout, not the parked worktree. Don't GC
the worktree the session is bound to — it breaks the live cwd; leave it for
session-end cleanup. Related: [[feedback_enterworktree_stuck_cwd]].
