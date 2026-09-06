---
name: feedback_isolated_session_cannot_read_shared_checkout
description: "In an EnterWorktree session the path guard blocks `git -C <primary>` for reads too, not just writes — so the shared checkout's dirty state is unknowable from inside; ExitWorktree first"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a95551ca-2f8f-4b22-8ca0-859f7bf1e1c2
  modified: 2026-08-14T13:57:53.304Z
---

During an `EnterWorktree` session, the worktree path guard refuses **every**
`git -C <shared-checkout>` invocation — `status --short` and `diff` included,
not only mutations. The deny text names redirection to the shared checkout, and
it does not distinguish read from write.

Consequence: **an isolated session cannot answer "what is dirty in the primary
checkout".** That matters because `sync-local-main.sh` refuses to fast-forward a
dirty checkout, and the one diagnostic you need is exactly the one the guard
withholds.

*Partly repaired since (ticket 0851, 2026-09-07):* the refusal used to read
"dirty or busy checkout" and name nothing. It now names the state and up to
three paths — tracked modifications with their files, an untracked/incoming
collision with the colliding path, anything else quoting git's own line. Read
that message before reaching for a workaround; it answers the common case. It
still caps at three paths and still cannot tell you what is *in* them, so the
rest of this entry stands unchanged.

**Why:** the workaround I reached for silently narrows the question. Without
`git status` you fall back to whatever partial evidence is at hand — the
session-start `gitStatus` snapshot, or a content diff of the file you happen to
suspect — and then answer as if it were the whole set. On 2026-08-14 that
produced a confident "the local modification is byte-identical, discarding it
loses nothing", handed to the author as a `git checkout --` command. There were
**three** modified files, not the one the snapshot named, and one of them held a
newer version than anything committed, carrying a lesson no branch had. The
command would have deleted it.

Note the shape: the session-start snapshot is not wrong, it is *stale and
partial*, and nothing about it announces that. It reads like an answer.

**How to apply:**
- When the shared checkout's state conditions a destructive step (discarding a
  modification, forcing a sync, `checkout --`), **`ExitWorktree` first**, then
  run `git status --short` where it works. The exit is cheap and reversible;
  the overwrite is not.
- Use `action: "keep"` if the exit balks about commits on the auto-created
  `worktree-<name>` branch — that branch is usually the one `EnterWorktree` made
  and you never used, but "usually" is not worth a discard.
- Before proposing a `git checkout --` / discard command **to the author**, say
  plainly whether you enumerated the set or inferred it. A command handed over
  carries your confidence with it, and the author has no way to see which of the
  two it rested on.
- Diffing the working tree against `origin/main` (not local `main`) is the check
  that matters: a stale local `main` marks files `M` that already match the
  remote, and hides that others differ.

The general form is [[feedback_verify_each_before_batch_action]] — inferring
from a sample to a set whose size was never established. This is the case where
the harness itself prevents establishing it, which is why the answer is to leave
the worktree rather than to reason harder.
