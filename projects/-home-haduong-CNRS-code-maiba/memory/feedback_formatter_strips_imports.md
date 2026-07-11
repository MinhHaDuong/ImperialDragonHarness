---
name: Bundle imports with usage in a single Edit
description: The PostToolUse formatter (ruff --fix) strips imports it judges unused between Edit calls; a multi-step "add import → then add usage" sequence loses the import.
type: feedback
originSessionId: 6c9f06c6-a3f7-479b-b581-076baff198c3
---
When the project's PostToolUse hook runs `ruff check --fix` after every
Edit, any import without a usage in the file at that moment gets stripped
before the next Edit fires. This bit me repeatedly in sessions on this
repo — most painfully when the first ticket-0012 executor agent stalled
in a "formatter loop" that I had to take over manually.

**Why:** when the user gives instructions like "I'll fix the bug in this PR", you should make it work in one Edit, atomic.
**How to apply:** when adding a new import to an existing file, include
its first usage in the same Edit call. Patterns that work:

- One Edit that replaces a region spanning imports AND the first
  call site (acceptable for small files; large old_strings).
- For larger refactors, use Write to replace the whole file at once.
- If split is unavoidable, anchor the import with `_ = imported_name`
  on a single line right after the import block, in the same Edit.
  Remove the anchor in a later Edit once a real usage exists.

Patterns that DON'T work:
- Edit 1 adds import → Edit 2 adds usage. Import is gone by Edit 2.
- Edit that adds import alongside a *commented-out* usage. Comments
  don't count.
