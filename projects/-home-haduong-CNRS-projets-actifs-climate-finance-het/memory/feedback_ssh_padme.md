---
name: feedback-ssh-padme
description: Can SSH from doudou to padme; always prepend PATH=$HOME/.local/bin (uv absent from non-interactive PATH)
metadata:
  type: feedback
---

I can SSH from doudou to padme — never claim "I can't reach padme".

**Why:** both machines are the author's; padme hosts the data/GPU side.
Non-interactive SSH skips the login profile, so `uv` (at `~/.local/bin/uv`)
is not on PATH.

**How to apply:** `ssh padme 'PATH=$HOME/.local/bin:$PATH <command>'` — prepend
the PATH on every non-interactive invocation. (Merged from
feedback_ssh_padme_path, dream consolidation 2026-07-10.)
