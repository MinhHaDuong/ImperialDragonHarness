---
name: feedback_git_existence_check
description: "Use `git cat-file -e <ref>:<path>` to test if a file exists at a ref — `git ls-tree <ref> <path> && echo` gives false positives"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8fe4d2ee-3096-4ace-bd8f-095bf3ee88e9
---

To test whether a path exists at a git ref, use `git cat-file -e <ref>:<path>` (exits non-zero if absent).

**Why:** `git ls-tree origin/main <path> && echo "EXISTS" || echo "MISSING"` lies — `git ls-tree` exits **0 even when the path matches nothing** (it just prints empty output), so the `&&` branch always fires "EXISTS". On 2026-05-26 this produced a false "2×2 builder is ON origin/main" reading that briefly derailed the parallel-work reconciliation; the file was actually absent. `git cat-file -e` (or checking ls-tree's *output*, not its exit code) is the correct existence probe.

**How to apply:** `git cat-file -e origin/main:src/foo.py 2>/dev/null && echo present || echo absent`.
