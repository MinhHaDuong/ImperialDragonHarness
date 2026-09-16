---
name: feedback-frozen-results-chmod
description: Read-only permissions on experiment output dirs are intentional integrity signals; never chmod without explicit confirmation
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 50c2ce3f-0238-462c-a0d3-09e18745eddd
---

Never run `chmod -R u+w` on experiment output directories to unblock `git pull` or other operations.

**Why:** Read-only permissions (`444` files, `555` dirs) on `experiments/outputs/` subdirectories are intentional — they mark frozen, immutable data artifacts. Stripping them treats an integrity signal as an obstacle.

**How to apply:** When `git pull` fails with "Permission denied" on experiment output files, stop and ask the user what git is trying to do to those files before touching permissions. The right fix is to understand and confirm the operation, not remove the protection.
