---
name: skill-commit-discipline
description: Skills that write to tracked files must include explicit git add/commit instructions — uncommitted writes leave repo dirty and block next beat cycle
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5250facb-47b9-467f-b3b4-8101e2151807
---

Skills that instruct the LLM to write tracked files (settings.json, scripts/beat.py, tickets/*.erg) must include explicit `git add && git commit` after each write.

**Why:** Uncommitted tracked files cause the beat pre-flight dirty-tree check (PR #207) to abort the next cycle. Observed overnight 2026-05-14→15 with nightbeat-supervisor; fixed in PR #208 (ticket 0164). Sweep found the same gap in nightbeat-report (ticket 0165).

**How to apply:** When writing or reviewing skill SKILL.md files, check every paragraph that mentions writing to a tracked file. If no commit instruction follows within the same action block, add one. The nightbeat-supervisor adherence test (`tests/test_nightbeat_supervisor_skill.py`) is the reference pattern — grep for write-point markers and assert `git add/commit` appears nearby.
