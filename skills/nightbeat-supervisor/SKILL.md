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

Outputs `{prs_to_merge, failures}`. If both are empty, update the watermark
and stop.

## 2. Merge ready PRs

For each entry in `prs_to_merge`:

1. Check the diff: `bash ~/.claude/skills/nightbeat-supervisor/check-pr-diff <pr> <repo>` — any non-zero exit is a HOLD; log the reason, skip to failures.
2. `/verify-gate <pr>` — APPROVED → `/merge <pr>`. REROLL → note on the linked ticket. ESCALATE → go to step 4.

## 3. Triage failures

Read the nightbeat log for each failure. In practice, `error_max_budget_usd`
is the only failure type observed across 60 runs (7/7 failures). Triage
accordingly:

**`error_max_budget_usd`** (all observed failures): read the last 50 lines of
the log to identify what consumed the budget — common sub-causes are `erg
check` surprises, STATE.md scope creep, and stale worktree cleanup. Raise the
per-project `ProjectConfig` field in `beat.py` by 20%, capped at 2× the
module-level constant; never touch the module-level constant. Stop the main
timer before editing, restart after.

**`permission_denials` non-empty** (not yet observed, tracked in outcomes
JSONL): add the denied command to `settings.json` allowlist.

**Anything else**: open a ticket with the log excerpt and the result record's
`subtype` and `stop_reason`; do not auto-repair.

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
