---
name: feedback_module_level_git_paths
description: Python scripts that run git rev-parse at module level silently write to the worktree instead of the main repo when imported from a worktree session
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6ab09d69-eba5-47b2-b403-1667f554095c
---

Do not resolve repo-root paths at module level in Python scripts. `git rev-parse --show-toplevel` runs at import time and resolves to the **worktree root**, not the main repo — so `STATE_FILE = REPO_ROOT / "STATE.md"` writes to the worktree silently.

**Why:** Discovered in ticket 0179 (`refresh-STATE.py`). The script appeared to succeed but left the main repo's STATE.md unchanged. The bug was silent — no error, just a write to the wrong location.

**How to apply:** Any Python script that derives a target file path from the repo root must accept the path as a CLI argument (argparse) or use the caller-provided path as the source of truth, with `git rev-parse` as the fallback only for interactive invocation. Pattern: `repo_root = Path(args.path) if args.path else _repo_root()`.
