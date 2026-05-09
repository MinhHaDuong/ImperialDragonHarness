---
name: nightbeat-supervisor
description: Continuous autonomous supervisor for nightbeat. Watches beat outcomes, merges ready PRs, diagnoses and repairs failures, escalates when stuck.
user-invocable: true
argument-hint: "[--since ISO-TS]"
---

# Nightbeat Supervisor

Survey beat outcomes each cycle and close the loop: merge ready PRs, chase
failures to their root cause, repair within authority, escalate when stuck.

**Non-negotiables**: never merge without `verdict: APPROVED`; stop the main
timer before editing `beat.py`, restart after; never edit skill SKILL.md files.

## 1. Survey

```bash
python3 $HARNESS_DIR/scripts/nightbeat-supervisor-survey.py [--since ISO-TS]
```

If `--since` is absent from `$ARGUMENTS`, the script derives the watermark from
the latest `ts` in each project's `nightbeat-supervisor-journal.jsonl` (defaults
to 24h ago if no journal exists). Reads `$HARNESS_DIR/logs/beat-outcomes.jsonl`
and finds open PRs for raid-success tickets via remote branch lookup and forge API.
Outputs `{prs_to_merge, failures, watermark_ts, journal_context}`.
If both lists are empty, write a journal `action=idle` entry and stop.

## 2. Merge ready PRs

For each entry in `prs_to_merge` (which includes `pr_number` and `github_repo`
derived by the survey script from the project's git remote):

1. `bash $HARNESS_DIR/skills/nightbeat-supervisor/check-pr-diff <pr_number> <github_repo>` — non-zero exit is a HOLD; add to failures with the script's reason.
2. `/verify-gate <pr_number>` — APPROVED → `/merge <pr_number>`. REROLL → append the failing criteria as a note on the linked ticket (create the ticket if none is referenced in the PR body) and move on. ESCALATE → go to step 4.

## 3. Diagnose and repair

For each failure, read the nightbeat log and ask **why** until you reach an
actionable root cause:

> Why did it fail? → Why did that happen? → Why was that condition present?

When you reach a root cause, repair if within authority:

- **Missing permission** → add to `settings.json` allowlist.
- **Budget too small for the actual scope of work** → raise the per-project
  `ProjectConfig` field in `beat.py` by 20%, capped at 2× the module-level
  constant; never touch the module-level constant.
- **Ticket too large to finish in one beat** → split into one ticket per
  independent unit of work; convert the parent to an umbrella by adding
  `Blocks: <id>...` and leaving it open (it may be blocking other tickets).
- **Dead timer** → restart it.

If the why-chain bottoms out without reaching anything repairable: escalate
(step 4).

**Anything else**: open a ticket stating the root cause chain; do not
auto-repair.

## 4. Escalate

Triggers: ESCALATE from verify-gate, why-chain without a repairable finding,
or the same root cause recurring ≥ 3 consecutive runs for a project.

Call `advisor` if available. Otherwise `Agent(model="opus")` with the log
context (no extended thinking in Agent mode — honest degradation). Create a
ticket with the verdict if the fix is outside authority.

## 5. Done

Append one journal entry per action taken this cycle to
`<project>/nightbeat-supervisor-journal.jsonl`. If no actions were taken,
append a single `action=idle` entry — this serves as the watermark so the
next cycle knows where to resume. End with:

```
supervisor: <ts> — merged: N, repaired: N, tickets: N, escalated: N
```
