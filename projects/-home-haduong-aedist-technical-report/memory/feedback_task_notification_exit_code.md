---
name: feedback-task-notification-exit-code
description: "Background task-notification \"completed (exit code 0)\" is the wrapper's exit, not the command's — read the verdict from the output file"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 39826929-4e74-43b7-9102-485e4fbcae1f
---

A `<task-notification>` saying "completed (exit code 0)" reports the shell
wrapper's exit (e.g. a trailing `echo "exit=$?"` succeeds even when make
failed). In the 0439 session this produced a false "full make check exit 0"
claim in a PR body, corrected later by comment.

**Why:** the notification summarizes the background *task*, not the inner
command; rtk output rewriting can also truncate the tail where the pytest
verdict lives.

**How to apply:** after any backgrounded `make check`/test run, read the
actual `exit=` line or the pytest summary from the task output file (or the
rtk tee log under `~/.local/share/rtk/tee/`) before reporting a verdict.
Never report green from the notification line alone.
