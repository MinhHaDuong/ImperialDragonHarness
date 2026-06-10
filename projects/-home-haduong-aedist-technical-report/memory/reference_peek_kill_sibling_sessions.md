---
name: reference-peek-kill-sibling-sessions
description: "How to observe, identify, and safely kill another local Claude Code session without killing yourself"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c86c1c3d-4c89-49f2-9d53-7bda12071fdd
---

There is **no built-in cross-session viewer** and no IPC to "connect to" or take
over another running session — each `claude` process is isolated (see
[[feedback-async-agent-continuation]]). You observe a sibling session only by its
**footprint**, and you identify it by **cwd**, never by guessing the PID.

**Peek at what a session is doing** — transcripts grow in real time under
`~/.claude/projects/<slugified-project>/<uuid>.jsonl`:
- `ls -lt <proj>/*.jsonl | head` — newest mtime = most active session.
- `tail -f <proj>/<uuid>.jsonl` — watch it think/act live.
- Render the tail (text / thinking / tool_use / tool_result) with a small Python
  parser; the most-recently-updated jsonl with *your own* last user message in it
  is THIS session.

**Identify which PID is which (critical before killing):**
- `ps -o pid,lstart,args -C claude` lists live sessions; a
  `claude daemon run --origin transient` entry is a harness daemon, **not** a
  session — leave it.
- `readlink /proc/<pid>/cwd` maps each PID to its worktree. **The PID whose cwd is
  your own worktree is you — do NOT kill it.**

**Safe to kill** when: the target is idle (its transcript stopped growing), its
work is already on `origin/main`, and there are no git locks
(`find .../worktrees -name index.lock -o -name HEAD.lock`). `kill <pid>`
(SIGTERM); `-9` only if it won't exit. Loses only unsaved *conversation* context —
committed code/tickets/memory survive. Remove its orphaned worktree *after* the
process is dead (`git worktree remove …`), never before (yanks files from a live
process).
