---
paths:
  - "STATE.md"
last-reviewed: 2026-07-13
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
| `## Status` | Ticket counts + awaiting-author + next picks · open MRs + CI verdict · last 3 first-parent commits | Machine |

**Replace policy — no append.** Each session rewrites `## Status` in full from current git state and bumps `Last updated:` in the preamble. All `##` sections after `## Status` are preserved verbatim. The other hand-edited sections are touched only when the author explicitly updates them.

**Line budget:** `## Status` ≤ 20 lines · total ≤ 40 lines. History lives in `git log`, full ticket list via `erg ready tickets/`.

## Automation level (decided 2026-07-13)

STATE refresh is **wrap-up-triggered only**: `/lair` step 10 runs
`scripts/refresh-STATE.py`. No cron or hook writes STATE.md.

- The script replaces the machine section only when the heading is exactly
  `## Status`.
- Adoption path: with no `## Status` heading, the script appends a generated
  one at the end of the file.
- A customized heading (`## Status: <title>`, `## Status snapshot`) marks a
  hand-maintained section: the script aborts without writing (exit 2). Rename
  the heading to exactly `## Status` to opt in to machine refresh.
- Projects with a divergent STATE converge at reactivation, when a session
  next works there — not by gratuitous churn while dormant.

## Minimal template

```markdown
Last updated: YYYY-MM-DDTHH:MMZ

## North star
[One paragraph. Why this project exists, what success looks like. Author-maintained.]

## Status
<!-- generated YYYY-MM-DDTHH:MMZ · as of sha -->
**Tickets:** N ready · N blocked · N awaiting author — `erg ready tickets/` for full list
  next: NNNN title · NNNN title
**In flight:** N open PRs (N draft), oldest #N Nd · CI main: success
**Recent (first-parent):**
  sha msg
  sha msg
```

The `as of` sha anchors the hand sections to the repo state they described —
catch up after dormancy with `git log --oneline <sha>..HEAD`. The in-flight
and CI facts come from the forge CLI and are omitted when it is unavailable;
the refresh never fails on their account.
