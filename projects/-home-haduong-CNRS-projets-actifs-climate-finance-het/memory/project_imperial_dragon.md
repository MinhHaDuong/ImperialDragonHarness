---
name: Imperial Dragon harness extraction
description: Workflow renamed from Dragon Dreaming to Imperial Dragon (5 claws); generic harness extracted to ~/.claude/ backed by ImperialDragonHarness repo
type: project
---

On 2026-04-01, the workflow was renamed from Dragon Dreaming (4 phases) to Imperial Dragon (5 claws):

1. Imagine (was Dreaming)
2. Plan (was Planning)
3. Execute (was first half of Doing)
4. Verify (was second half of Doing — PR is the interface)
5. Celebrate (was Celebrating — now includes memory consolidation/"dreaming forward")

Generic rules, skills, hooks extracted from project `.claude/` to user-level `~/.claude/`, backed by https://github.com/MinhHaDuong/ImperialDragonHarness.

**Why:** Harness was project-locked; needed to be reusable across projects. "Dreaming" conflicted with memory consolidation in Celebrate phase. Doing split because PR is a natural boundary between execution and verification.

**How to apply:** Use Imperial Dragon phase names in all announcements. User-level skills/rules load automatically — project `.claude/` only has project-specific residuals. PR #628 on Oeconomia repo.
