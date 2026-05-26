---
name: feedback_xargs_env_var
description: xargs does not interpret shell variable assignment syntax; use env prefix
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 50c2ce3f-0238-462c-a0d3-09e18745eddd
---

`xargs` treats `VAR=value cmd` as a command, not a shell assignment. Always prefix with `env VAR=value cmd` when passing env vars through xargs.

**Why:** `xargs -P N -I{} PYTHONPATH=.. uv run ...` fails with "No such file or directory" because xargs tries to execute `PYTHONPATH=..` as a binary.

**How to apply:** In Makefiles where xargs fans out commands, define `UV_RUN := env PYTHONPATH=.. uv run ...` so the `env` prefix is always present.
