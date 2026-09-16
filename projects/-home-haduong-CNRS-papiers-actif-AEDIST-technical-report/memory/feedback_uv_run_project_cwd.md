---
name: feedback_uv_run_project_cwd
description: uv run --project does not change cwd but relative paths in spawned process may resolve differently
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 50c2ce3f-0238-462c-a0d3-09e18745eddd
---

`uv run --project ..` does NOT change the working directory (confirmed empirically). However, when relative paths are passed as CLI args to the spawned Python process, they resolve against the actual cwd — so paths that look correct in the shell work fine.

The confusion: when using xargs from a Makefile, the `jobs/` relative path works IF the Makefile is invoked from the correct directory. Use `$(CURDIR)/jobs/` (absolute) in Makefiles to be safe.

**Why:** Three successive "Queue drained" failures traced to relative job path not resolving when workers spawned via xargs from a different cwd than expected.

**How to apply:** In experiment Makefiles, always use `$(CURDIR)` for job directory paths passed to worker CLI.
