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

Failure types ordered by observed frequency across all projects and 200+
beat-log entries. Read the nightbeat log for each failure, classify, and act:

**`aborted` with no diagnostics** (most common — 22 observed, usually a
timer-stop cascade): check whether the main timer is still active. If stopped,
restart it. If already running, this is noise from a mid-run kill; no action.

**`error_max_budget_usd`** (7 observed, always during housekeeping or raid):
read the last 50 lines of the log to identify the sub-cause — observed
triggers are `erg check` surprises, STATE.md scope creep, and stale worktree
cleanup. Raise the per-project `ProjectConfig` field in `beat.py` by 20%,
capped at 2× the module-level constant; never edit the module-level constant.
Stop the main timer before editing, restart after.

**`aborted` with stale-in-progress diagnostics** (8 observed — SIGKILL
recovery): self-resolving; beat.py handles this on the next run. Log it, no
action unless it recurs more than twice in the same window.

**Same ticket failing repeatedly** (observed: chemin-de-voix ticket 0021,
3× in a row): the ticket is likely underspecified or blocked. Add a sweep-skip
via `erg note sweep-skip: <reason>` and open a repair ticket.

**`failed` with no ticket_id** (5 observed — housekeeping or pick-ticket died
before a ticket was selected): read the log to identify which phase failed.
Treat as `error_max_budget_usd` if the phase signal is budget; otherwise open
a ticket.

**`permission_denials` non-empty** (not yet observed, tracked in outcomes
JSONL): add the denied command to `settings.json` allowlist.

**Anything else**: open a ticket with the log excerpt; do not auto-repair.

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
