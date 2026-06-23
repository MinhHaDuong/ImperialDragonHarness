---
name: No --no-verify shortcuts
description: Never bypass pre-commit hooks to amend on main; always branch first
type: feedback
---

Don't use `--no-verify` to work around the main-branch guard in pre-commit hooks. Even for "quick" amends, create a branch, commit there, and merge back.

**Why:** The main-branch guard exists for a reason. Bypassing it led to a messy amend that had to be undone via reflog. The user explicitly asked to undo it.

**How to apply:** When files need to be added to a recent commit on main, create a branch from HEAD, commit there, then merge `--no-ff` back. Never suggest `--no-verify` as the first option.
