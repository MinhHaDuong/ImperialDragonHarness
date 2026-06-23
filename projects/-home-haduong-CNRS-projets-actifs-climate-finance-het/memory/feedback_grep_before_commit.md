---
name: grep before committing fixes
description: When fixing a pattern (e.g. wrong model name), grep the whole project before committing — don't rely on finding all instances by reading individual files
type: feedback
---

When fixing a recurring error (like SPECTER2 → bge-m3), always do a project-wide grep before the first commit. The first commit in PR #629 missed two occurrences in the same file because only the lines near the initial find were checked.

**Why:** Review caught it, but it cost an extra commit and review cycle.
**How to apply:** Before any "fix X across files" commit, run `Grep` for the pattern with no path restriction.
