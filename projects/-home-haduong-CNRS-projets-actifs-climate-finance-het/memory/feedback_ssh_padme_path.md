---
name: Always prepend PATH for padme SSH commands
description: Non-interactive SSH to padme doesn't source .bashrc — uv, make targets using uv all fail without explicit PATH
type: feedback
originSessionId: 5171a15b-fd7c-4404-981c-490a8509eab5
---
Always prepend `export PATH=$HOME/.local/bin:$PATH` when running commands on padme via SSH.
`uv` is at `~/.local/bin/uv` which is not in the default PATH for non-interactive sessions.
This affects `make` targets that call `uv run`, not just direct `uv` invocations.

**Why:** Repeated failures — `uv: command not found` — when running `make manuscript`, `make divergence-tables`, etc. via `ssh padme "cd ~/Climate_finance && make ..."`.

**How to apply:** Every `ssh padme` command that might invoke `uv` (directly or via Make) must include the PATH export. Use: `ssh padme "export PATH=\$HOME/.local/bin:\$PATH && cd ~/Climate_finance && make ..."`.
