---
name: SSH to padme is available
description: Can SSH from doudou to padme to check progress, run commands, monitor pipeline
type: feedback
---

SSH to padme works from doudou: `ssh padme '...'`. Use it to check pipeline progress, tail logs, inspect processes.

**Why:** User pointed out that bash + ssh means we can monitor padme directly — don't say "I can't reach padme."

**How to apply:** When the user asks to check padme status, use `ssh padme` directly. Remember `uv` is at `~/.local/bin/uv` (not in PATH for non-interactive SSH). Repo is at `~/Oeconomia-Climate-finance`.
