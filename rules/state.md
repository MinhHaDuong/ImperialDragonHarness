---
paths:
  - "STATE.md"
last-reviewed: 2026-10-19
---

# STATE.md

Single orientation file, loaded at session start via hook. Hard cap: **40 lines total**. History lives in `git log`.

## Structure

Every section is hand-written:

| Section | Content | Who edits |
|---------|---------|-----------|
| `## North star` | One paragraph — the core argument, rarely changes | Author |
| Any additional `##` sections | Milestones, blockers, incidents, decisions, next actions in prose — author adds as needed | Author |

**No derived numbers (ticket 1121).** STATE.md stores no ticket counts, next
picks, open merge requests, CI verdicts or recent commits: every merge made
them stale and every parallel PR collided on them. One pointer line replaces
them — live numbers are read when needed from `erg ready tickets/`,
`erg list` and `/dashboard`. Nothing regenerates STATE.md; `/lair` step 10
bumps `Last updated:` and prunes the hand sections. A ticket-closing PR needs
no STATE.md edit.

**Live counts at session start.** `scripts/on-start-context.sh` prints one line of
open and ready ticket counts, computed from local `erg` at read time, so the
session still sees them without a committed copy. Only runtimes whose
session-start hook runs `on-start-context.sh` see that line: Claude Code (SessionStart
hook), Codex (`SessionStart` in `adapters/codex/hooks.json`) and Pi (the
`session_start` handler in `adapters/pi/extensions/idh-guard.ts`, delivered with
the first user turn) all do.

**Line budget:** total ≤ 40 lines. History lives in `git log`.

The former `state-metrics` extension point (a project make target whose
output was appended to a generated `## Status` block) is retired with that
block: project metrics are derived numbers too. A project that wants them
prints them on demand.

## Minimal template

```markdown
Last updated: YYYY-MM-DDTHH:MMZ

## North star
[One paragraph. Why this project exists, what success looks like. Author-maintained.]

Live counts: `erg ready tickets/` · `erg list` · `/dashboard`.

## Next
[Blockers, decisions, next actions in prose.]
```
