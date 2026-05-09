---
paths:
  - "STATE.md"
last-reviewed: 2026-05-09
---

# STATE.md

Single orientation file, loaded at session start via hook. Hard cap: **40 lines total**. History lives in `git log`.

## Structure

Hand-edited sections (stable, owned by the author):

| Section | Content | Who edits |
|---------|---------|-----------|
| `## North star` | One paragraph — the core argument, rarely changes | Author |
| Any additional `##` sections | Milestones, blockers, incidents, next actions, backlog — author adds as needed | Author |

One mechanically generated section (replaced each session from `git log` + `git-erg`):

| Section | Content | Who edits |
|---------|---------|-----------|
| `## Status` | Ticket summary counts + last 3–5 commits | Machine |

**Replace policy — no append.** Each session rewrites `## Status` in full from current git state. All `##` sections after `## Status` are preserved verbatim — the script only replaces the Status body, not what follows. The hand-edited sections are touched only when the author explicitly updates them.

**Line budget:** `## Status` ≤ 20 lines · total ≤ 40 lines. History lives in `git log`, full ticket list via `erg ready tickets/`.

## Minimal template

```markdown
Last updated: YYYY-MM-DDTHH:MMZ

## North star
[One paragraph. Why this project exists, what success looks like. Author-maintained.]

## Status
<!-- generated YYYY-MM-DDTHH:MMZ -->
**Tickets:** N ready · N blocked — `erg ready tickets/` for full list
**Recent commits:**
  sha msg
  sha msg
```
