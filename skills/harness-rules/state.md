---
paths:
  - "STATE.md"
last-reviewed: 2026-05-09
---

# STATE.md

Single orientation file, loaded at session start via hook. Hard cap: **40 lines total**. History lives in `git log`.

## Structure

Two hand-edited sections (short, stable, owned by the author):

| Section | Content | Who edits |
|---------|---------|-----------|
| `## North star` | One paragraph — the core argument, rarely changes | Author |
| `## Milestones` | Current + next milestone, `- [ ]` checkboxes, 5–8 lines max | Author |

One mechanically generated section (replaced each session from `git log` + `git-erg`):

| Section | Content | Who edits |
|---------|---------|-----------|
| `## Status` | Open tickets (git-erg), last 3–5 commits (git log --oneline), current blockers | Machine |

**Replace policy — no append.** Each session rewrites `## Status` in full from current git state. The hand-edited sections are touched only when the author explicitly updates them. No "Completed" or "Backlog" sections — git has the history, tickets have the backlog.

**Line budget:** `## North star` ≤ 5 lines · `## Milestones` ≤ 10 lines · `## Status` ≤ 20 lines · header/whitespace ≤ 5 lines.

## Template

```markdown
Last updated: YYYY-MM-DD

## North star
[One paragraph. Why this project exists, what success looks like. Author-maintained.]

## Milestones
### Current: [name]
- [ ] item
- [x] done item

### Next: [name]
- [ ] item

## Status
<!-- generated: git log --oneline -5 + git-erg open -->
**Open tickets:** 0NN title · 0NN title · …
**Recent commits:** sha msg · sha msg · …
**Blockers:** ticket or "None"
```
