---
name: project_statusline_command_no_tilde_expansion
description: settings.json statusLine.command must use $HOME, not ~ — some invokers skip shell expansion
metadata:
  type: project
---

`settings.json`'s `statusLine.command` field must use `$HOME/.claude/...`, not `~/.claude/...`, matching every other command entry in the file.

**Why:** `/gaze` round 1 on PR #648 flagged this as a real risk, not a style nit: if the invoker spawns the command without shell interpretation, `~` never expands and the status line silently goes blank — defeating the whole point of the config. Fixed in commit `4a274a9`.

**How to apply:** when adding or editing any `command` entry in `settings.json` (statusLine, hooks, etc.), grep the file for the existing convention first (`$HOME` here) and match it rather than defaulting to `~`.
