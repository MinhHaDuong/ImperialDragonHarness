---
name: skill-doctor
description: "Weekly failure-pattern analysis across journals, logs, and git history. Clusters recurring failures and opens tickets with proposed patches. Never auto-applies fixes."
user-invocable: true
argument-hint: "[--days N]"
model: sonnet
effort: medium
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

| Rank | Signature | Freq | Sev | Score | Status | Affected Skill | Root Cause |
|------|-----------|------|-----|-------|--------|----------------|------------|

For each `uncovered` pattern, show:
- **Evidence**: the `evidence` array from the survey (verbatim log/journal excerpts)
- **Candidate patch**: the proposed fix from the survey
- **Expected impact**: estimated failure-rate reduction

Ask the user which patterns to ticket before proceeding.

### Root-cause taxonomy

The `Root Cause` column tags each pattern with a shared label for *why* it
recurs (source: arXiv:2604.21965 §5.3, reframed for the harness, ticket 0291).
Assign it when you author the report table — a labeling convention, like the
`Status` column, not a mechanical detector. Same vocabulary as verify-gate's
`root_cause_class`:

- **Agent Error** — an agent misapplied a rule it had. E.g. a supervisor kept
  re-raising its own budget.
- **Extractor Error** — a skill or convention was underspecified. E.g. the merge
  convention never pinned the exact `**Ticket:**` string.
- **Original Error** — a pre-existing gap the failures expose. E.g. a missing
  dirty-tree guard that predates the incidents.
- **Missing Data** — the survey lacked context. E.g. it re-flagged already-fixed
  issues for want of a canonical path.
- **Other** — cause undetermined from the log context.

## 4. Open tickets

Apply the severity floor (rules/workflow.md § Autonomous Action Rules), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.

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
