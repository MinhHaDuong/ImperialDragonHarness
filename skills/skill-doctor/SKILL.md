---
name: skill-doctor
description: Weekly failure-pattern analysis across journals, logs, and git history. Clusters recurring failures and opens tickets with proposed patches. Never auto-applies fixes.
user-invocable: true
argument-hint: "[--days N]"
model: sonnet
---

# Skill Doctor $ARGUMENTS

Analyze recurring failure patterns across the harness automation and propose
hardening patches via tickets. Run weekly or on-demand.

**Authority boundary**: propose only — open tickets with diffs, never
auto-apply patches. Same boundary as nightbeat-supervisor's "anything else →
open a ticket."

## 1. Survey

```bash
python3 $HARNESS_DIR/scripts/skill-doctor-survey.py $ARGUMENTS
```

Parse the JSON output. If `pattern_count` is 0, report "no recurring patterns
found" and stop.

## 2. Cross-reference existing tickets

For each pattern in `patterns`, search open tickets for the `signature` keyword:

```bash
ERG=$(command -v erg 2>/dev/null || echo "tickets/erg")
$ERG ready --json tickets/ 2>/dev/null || true
```

Also check closed tickets for recent fixes:

```bash
grep -rl "<signature>" tickets/closed/ 2>/dev/null | tail -5
```

Mark each pattern as `covered` (open ticket exists), `recently-fixed`
(closed ticket within 14 days), or `uncovered`.

## 3. Report

Present the ranked patterns as a table:

| Rank | Signature | Freq | Sev | Score | Status | Affected Skill |
|------|-----------|------|-----|-------|--------|----------------|

For each `uncovered` pattern, show:
- **Evidence**: the `evidence` array from the survey (verbatim log/journal excerpts)
- **Candidate patch**: the proposed fix from the survey
- **Expected impact**: estimated failure-rate reduction

Ask the user which patterns to ticket before proceeding.

## 4. Open tickets

For each approved pattern, create a ticket via `tickets/erg new "<title>"`:

- **Title**: `skill-doctor: {signature} — {one-line fix summary}`
- **Context**: evidence from the survey, frequency × severity score,
  affected skill/script
- **Actions**: the candidate patch, broken into concrete steps
- **Test**: how to verify the fix prevents recurrence (ideally a
  grep-able assertion or a test case)
- **Exit criteria**: the specific condition that makes this pattern
  stop recurring

Commit all new tickets in a single commit:
`chore(skill-doctor): open N tickets from weekly survey`

## 5. Done

Report:
```
skill-doctor: surveyed {days}d window — {pattern_count} patterns, {uncovered} uncovered, {ticketed} tickets opened
```
