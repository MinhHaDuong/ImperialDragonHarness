---
name: pipe-masks-exit-code
description: "Piping a build/test command through `| tail` reports the pipe's exit code, not the command's — background tasks then notify \"completed (exit 0)\" on failure"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 565b2902-f291-41d1-9605-a19fdbe15894
  modified: 2026-07-29T17:49:47.581Z
---

Running `make corpus 2>&1 | tail -100` or `make check | tail -25` in a background task makes the harness report tail's exit code (0), so a failed pipeline or test suite notifies as "completed". Bit twice on 2026-07-29: a CUDA-OOM `dvc repro` failure and a 1-failed `make check` both arrived as exit 0.

**Why:** the shell returns the last pipe stage's status unless `set -o pipefail` is active; background-task notifications key on that status.

**How to apply:** run the command bare (the output file already captures everything) or prefix with `set -o pipefail;`. Verify outcomes from the log tail, never from the exit-0 notification alone. Related: [[This machine is padme]].
