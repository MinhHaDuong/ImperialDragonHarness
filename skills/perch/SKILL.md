---
name: perch
description: Mid-session orientation — summarize what's done, surface unresolved points. Not a session wrap-up; no side effects.
user-invocable: true
argument-hint:
---

# Perch — mid-session position check

A fast, read-only report. Run at any point to re-orient. No files written, no tickets opened, no branches pushed.

## Steps

1. **Ground in git.** Run `git log --oneline --since="6am" 2>/dev/null || git log --oneline -10`. List commits made in this session.

2. **Report: Done.** What is concretely finished in this conversation:
   - Files written or edited (from conversation context).
   - Commits and PRs merged.
   - Tickets closed.
   - Decisions reached.
   Items only. No prose.

3. **Report: Open.** Raised but not finished:
   - Work mentioned but not started or deferred to "next session".
   - Issues discovered but not fixed.
   - Docs or state noted as stale.
   - Questions asked and not answered.
   Items only. Be specific — a vague "follow-up needed" is useless.

4. **Report: Drift** (only if present). Topics that diverged from the original goal:
   - Scope creep or mid-session pivots.
   - Side-quests that consumed time.
   - New tickets or tickets opened during the session that weren't the original target.
   Omit this section entirely if there was no drift.

5. **One-line stance.** End with a single sentence: where things stand right now and what the natural next move is.

## Output shape

```
## Done
- …

## Open
- …

## Drift  ← omit if none
- …

**Stance:** [one sentence]
```

No headers beyond these. No preamble. No "Here is a summary of…" opener.
