---
name: nightbeat-supervisor
description: Continuous autonomous supervisor for nightbeat. Watches beat outcomes, merges ready PRs, diagnoses and repairs failures, escalates when stuck.
user-invocable: true
argument-hint: "[--since ISO-TS]"
---

# Nightbeat Supervisor

Watch `~/.claude/logs/beat-outcomes.jsonl` for unprocessed entries and close
the loop: merge PRs that are ready, diagnose failures, repair within authority,
escalate when stuck.

**Non-negotiables**: never merge without `verdict: APPROVED`; auto-edit only
`settings.json` permissions block and per-project `ProjectConfig` literals —
everything else opens a ticket; stop the main timer before touching `beat.py`,
restart after.

## 1. Survey

```bash
python3 ~/.claude/scripts/nightbeat-supervisor-survey.py [--since ISO-TS]
```

Reads both `~/.claude/logs/beat-outcomes.jsonl` (phase-level signals) and
each project's `beat-log.jsonl` (beat-level signals). Outputs
`{prs_to_merge, failures}`. If both are empty, update the watermark and stop.

## 2. Merge ready PRs

For each entry in `prs_to_merge`:

1. Check the diff: `bash ~/.claude/skills/nightbeat-supervisor/check-pr-diff <pr> <repo>` — any non-zero exit is a HOLD; log the reason, skip to failures.
2. `/verify-gate <pr>` — APPROVED → `/merge <pr>`. REROLL → note on the linked ticket. ESCALATE → go to step 4.

## 3. Triage failures

For each failure, read the log and ask **why** until you reach an actionable
root cause. Do not stop at the signal — `error_max_budget_usd` is not a root
cause, it is a symptom. Keep asking:

> Why did it fail? → Why did that happen? → Why was that condition present?

Stop when you reach something the harness can change. Then either repair
within authority or open a ticket naming the root cause, not the symptom.

**Repair authority** (auto-apply without a ticket):
- Root cause is a missing permission → add to `settings.json` allowlist.
- Root cause is a scope that fit under a larger budget → raise the per-project
  `ProjectConfig` field by 20%, capped at 2× the module-level constant; never
  touch the module-level constant; stop the timer first, restart after.
- Root cause is a ticket too large to finish in one beat → read the body; if
  it has obvious split lines (independent deliverables, self-contained
  sections), split into two child tickets and close the parent; otherwise
  add a sweep-skip and open a repair ticket.
- Root cause is a dead timer → restart it.

**Everything else**: open a ticket stating the root cause chain. Do not
auto-repair.

## 4. Escalate

When: ESCALATE verdict, unknown failure category, or the same failure type
recurring ≥ 3 consecutive runs for a project.

Call `advisor` if available. Otherwise: `Agent(model="opus")` with the log
context (no extended thinking in Agent mode — honest degradation). Create a
ticket with the verdict if the fix is outside auto-apply authority.

## 5. Done

Update the watermark. End with:
```
supervisor: <ts> — merged: N, repaired: N, tickets: N, escalated: N
```
