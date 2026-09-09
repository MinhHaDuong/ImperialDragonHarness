---
name: feedback_ask_the_live_peer_before_committing_its_work
description: "Uncommitted work in a shared checkout has an owner you can find and message; asking it beat every inference a file scan could make, twice in one hour"
metadata:
  node_type: memory
  type: feedback
---

Another session's uncommitted files sat in `~/.claude` blocking a fast-forward.
A file scan says only what is on disk: two paths, one new note and one index
line, static for thirteen minutes, no process holding the checkout. That reads
as orphaned, and committing it looks safe.

It was not orphaned. The note's own frontmatter carried
`originSessionId`, which names a transcript under
`~/.claude/projects/<cwd-key>/<id>.jsonl`; that transcript had been written one
minute earlier, and `ListAgents` showed the session live and busy. One
`SendMessage` got an answer in under a minute: land it, it is finished.

**Why:** asking bought two things no inspection of the working tree could
have produced, and both were load-bearing.

- The peer's index file was stale — based on a commit two merges old. Taking
  it as it stood would have reverted a consolidation that had merged an hour
  earlier. The peer confirmed it would not have caught that itself, because
  nothing in its own session showed main had moved.
- The peer had produced *more* than the two paths implied. A second finished
  note existed that I had not copied, and it had edited a third file — one I
  had just turned into a tombstone — adding two findings the consolidation
  lacked. A plain sync would have dropped both silently, with no conflict and
  no error.

Neither of those is visible from mtimes, `git status`, or process lists. The
scan was accurate and the conclusion it invited was wrong.

**How to apply:** when uncommitted work in a shared checkout is not yours,
find the owner before deciding anything. Read `originSessionId` from the file's
frontmatter, or match the checkout's transcripts by recency; `ListAgents` says
whether that session is alive; `SendMessage` reaches it by name. Ask whether it
is finished and whether you should land it, and say what you found — a peer
that knows main has moved will not hand you a stale file. Then enumerate *all*
its untracked paths rather than the ones you happened to notice, and merge its
index by appending only its added lines onto main's copy, never by taking its
whole file.

Silence is a reason to look harder, not a licence: a file untouched for
thirteen minutes belonged to a session mid-turn, while an hour of silence on a
different day did mean the session had ended. Age is weak evidence either way,
and the transcript settles it in one command. If the owner is genuinely gone,
land the work for it and say so; the cost of asking is a minute, and the cost
of not asking here would have been a reverted merge and two lost findings.

Related: [[feedback_shared_worktree_live_session_contention]] for the same
sharing hazard one layer down, where a peer switches the branch under you
between two commands.
