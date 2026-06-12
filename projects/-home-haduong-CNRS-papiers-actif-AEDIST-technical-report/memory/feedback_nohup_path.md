---
name: nohup strips PATH on padme
description: nohup on padme loses ~/.local/bin from PATH — uv not found. Always export PATH explicitly.
type: feedback
---

When launching background jobs on padme via `nohup`, `~/.local/bin` is not on PATH. `uv` lives there.

**Why:** nohup starts a minimal shell that doesn't source `.bashrc` / `.profile`.

**How to apply:** Always prepend PATH when launching nohup jobs on padme:
```bash
export PATH=$HOME/.local/bin:$PATH && nohup make ... > log 2>&1 &
```
