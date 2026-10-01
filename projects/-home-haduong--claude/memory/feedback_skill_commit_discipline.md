---
name: skill-commit-discipline
description: Skills that write to tracked files must include explicit git add/commit instructions — uncommitted writes leave the checkout dirty and block whatever runs next on it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5250facb-47b9-467f-b3b4-8101e2151807
---

Skills that instruct the LLM to write tracked files (settings.json, scripts, tickets/*.erg) must include explicit `git add && git commit` after each write.

**Why:** An uncommitted tracked file outlives the run and blocks the next consumer of that checkout: in 2026-05 it aborted the nightbeat cycle's dirty-tree pre-flight (PR #207/#208, tickets 0164/0165); the nightbeat is gone (ticket 0882), but the daily-pull timer still cannot update a dirty primary checkout (see `scripts/check-primary-checkout.sh`).

**How to apply:** When writing or reviewing skill SKILL.md files, check every paragraph that mentions writing to a tracked file. If no commit instruction follows within the same action block, add one.
