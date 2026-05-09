---
name: nightbeat-supervisor
description: Continuous autonomous supervisor for nightbeat. Watches beat outcomes, merges ready PRs, diagnoses and repairs failures, escalates when stuck.
user-invocable: true
argument-hint: "[--since ISO-TS]"
---

# Nightbeat Supervisor

Autonomous night watchman. Runs on its own 15-min timer (separate from
beat.py) and acts on every unprocessed outcome:

- **Happy path**: raid succeeded → PR open → verify-gate → merge.
- **Failure path**: housekeeping/raid failed → diagnose → auto-repair or
  ticket → escalate if stuck.

**Persona constraints** (non-negotiable, never override):
- Never merge without an explicit `verdict: APPROVED` from `/verify-gate`.
- Auto-edit only: `settings.json` permissions block, per-project `ProjectConfig`
  literals in `beat.py`. Everything else opens a ticket and stops.
- Never touch `beat.py` without stopping the main timer first and restarting
  it after.
- Never force-push.
- If the same failure type recurs ≥ 3 consecutive runs: escalate (Phase 6),
  stop acting autonomously on that failure type.

---

## Phase 1 — Lock + watermark load

Acquire an exclusive lock before any reads or writes:

```bash
exec 9>"${HOME}/.claude/logs/.supervisor.lock"
flock -n 9 || { echo "supervisor: already running, exiting"; exit 0; }
```

Read `~/.claude/logs/nightbeat-supervisor-watermark.json`. Extract `since`
(ISO-8601 timestamp). If the file does not exist, default `since` to 24 hours
ago. If `$ARGUMENTS` contains `--since <ts>`, use that value instead (allows
manual backfill).

```bash
python3 ~/.claude/scripts/nightbeat-supervisor-survey.py \
  --since "$SINCE" \
  --outcomes ~/.claude/logs/beat-outcomes.jsonl
```

Parse the JSON output. It contains three lists:
- `prs_to_merge` — `{project, ticket_id, pr_number, pr_sha, branch}`
- `failures` — `{project, ticket_id, phase, outcome, ts, log_file}`
- `idle` — informational only, skip

If both `prs_to_merge` and `failures` are empty: update the watermark to now
and stop. Log one line: `supervisor: no pending actions since <since>`.

---

## Phase 2 — Destructive-diff check (for each PR)

For each entry in `prs_to_merge`, before calling verify-gate, run the diff
check script:

```bash
bash ~/.claude/skills/nightbeat-supervisor/check-pr-diff "$PR_NUMBER" "$REPO"
```

The script exits 0 if the diff is clean, 1 if it contains a ticket deletion
without a corresponding move to `tickets/closed/`. It prints a one-line
reason to stdout.

If exit code is non-zero (1 = ticket deletion detected, 2 = fetch failed):
- Do NOT call verify-gate or merge regardless of reason.
- Create a note in the supervisor log: `HOLD PR#<n>: <reason from script stdout>`.
- Add it to the failures list for diagnosis in Phase 4.

Continue to next PR.

---

## Phase 3 — Merge loop

Process each PR that passed the destructive-diff check.

### 3a. Verify-gate

```
/verify-gate <pr_number>
```

Wait for verdict. Parse the last structured output block:
- `verdict: APPROVED` → proceed to merge.
- `verdict: REROLL` → do not merge. Log the failing criteria. If a ticket
  exists for this PR's work, append a `note` to it with the REROLL reason.
  If no ticket exists, create one.
- `verdict: ESCALATE` → do not merge. Escalate (Phase 6) with the full
  verify-gate output as context.

### 3b. Merge

```
/merge <pr_number>
```

If merge fails (non-zero exit): log the error, do not retry. Create a repair
note. Supervisor continues to next PR.

Log one line per merged PR: `supervisor: merged PR#<n> ticket=<id> project=<project>`.

---

## Phase 4 — Failure triage

For each entry in `failures`, read the corresponding log file:

```bash
cat ~/.claude/logs/nightbeat/<log_file>
```

Classify the failure into one of these categories:

| Category | Detection pattern |
|---|---|
| `permission_denial` | `permission_denials` field non-empty, or "Permission denied" in log |
| `budget_exhaustion` | `outcome=error_max_budget_usd`, or log ends mid-skill |
| `misplaced_tickets` | `erg check` output listing closed tickets not in `tickets/closed/` |
| `skill_bug` | Non-zero exit without budget/permission signal; log shows traceback or assertion |
| `spec_gap` | Raid ends with a question, or ticket exit criteria ambiguous in the log |
| `crash` | `aborted` outcome within CRASH_RECOVERY_WINDOW_S of `in_progress` |
| `unknown` | None of the above |

Record the classification. Then apply the repair strategy below.

---

## Phase 5 — Auto-repair (bounded authority)

Apply only within the authority bounds defined below. Anything outside the
bounds → create a ticket (see Phase 5d) and stop.

### 5a. Permission denial

Find the denied command in the log. Add it to the `allow` list in
`~/.claude/settings.json` under the appropriate hook, following the existing
allowlist structure.

```bash
python3 -c "import json,sys; d=json.load(open('${HOME}/.claude/settings.json')); print(json.dumps(d.get('permissions',{}), indent=2))"
```

Edit the file directly. Commit: `chore: supervisor auto-allow <command>`.

### 5b. Budget exhaustion

Locate the project's per-project `ProjectConfig` entry in `beat.py`
(search for `ProjectConfig(path=Path.home() / "<project-name>"`). Do not
touch module-level constants (`BUDGET_HOUSEKEEPING`, `BUDGET_RAID`, etc.) —
those affect every project.

If no per-project `ProjectConfig` exists for the failing project: create one
that copies the current global defaults, then raise only the relevant field
(e.g., `budget_housekeeping=0.90`). Do not auto-raise otherwise.

**Gate**: raise is at most 2× the module-level constant for that field. If
the per-project value is already at or above 2× the module-level constant,
do not auto-raise. Create a ticket instead.

Before editing `beat.py`:
```bash
systemctl --user stop claude-nightbeat.timer
```

Edit the `ProjectConfig` field only. Commit: `chore: supervisor raises budget for <project>`.

After commit:
```bash
systemctl --user start claude-nightbeat.timer
```

If `start` fails: log the error, leave timer stopped, create a diagnostic
ticket.

### 5c. Misplaced tickets

Run `erg check tickets/` to identify closed tickets not in `tickets/closed/`.
For each:

```bash
git mv tickets/<id>-<slug>.erg tickets/closed/<id>-<slug>.erg
```

Commit: `chore: supervisor moves closed tickets to tickets/closed/`.

Do not edit ticket content. Only move.

### 5d. Skill bug / spec gap / unknown

Do not auto-edit. Instead:

Search open tickets for a related title (grep by category keyword). If none
exists, create a new ticket using the erg binary:

```bash
ERG=${ERG:-tickets/erg}
$ERG new "Supervisor-flagged: <category> in <project>/<phase>"
```

Then add the log excerpt and classification to the ticket body.

Commit: `chore: supervisor creates repair ticket <id>`.

### 5e. Crash

Check if the main timer is currently stopped:

```bash
systemctl --user is-active claude-nightbeat.timer
```

If inactive: restart it.

```bash
systemctl --user start claude-nightbeat.timer
```

Log: `supervisor: restarted nightbeat timer after crash recovery`.

---

## Phase 6 — Escalate

Call this phase when:
- `verdict: ESCALATE` from verify-gate.
- `unknown` failure classification after Phase 4.
- Same failure type recorded ≥ 3 consecutive times in `failures` for the
  same project.

Collect:
1. The classification and log excerpt (last 100 lines of the log file).
2. Recent beat-outcomes entries for the project (last 7 days).
3. Any related open tickets.

**If the `advisor` tool is available** (interactive session): call it. It
forwards the full conversation transcript and uses a stronger reviewer with
extended thinking — the strongest escalation path.

**If `advisor` is not available** (typical for `claude -p bypassPermissions`
launched from the systemd unit): spawn a sub-agent on Opus:

```
Agent(
  subagent_type="general-purpose",
  model="opus",
  prompt="<assembled context above>"
)
```

Note: the Agent tool does not expose an `effort` field — this gives Opus 4.7
but without max-thinking mode. It is a degraded but useful fallback.

Apply the recommendation if it falls within auto-apply authority (Phase 5).
Otherwise: create a ticket capturing the diagnosis and recommended action.

Log: `supervisor: escalated <project>/<phase> failure — advisor=<yes|sub-agent> verdict: <one-line summary>`.

---

## Phase 7 — Watermark update

After all phases complete (even if some items failed), write the watermark:

```bash
python3 -c "
import json, datetime
wm = {'since': datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}
open('${HOME}/.claude/logs/nightbeat-supervisor-watermark.json', 'w').write(json.dumps(wm))
print('supervisor: watermark updated to', wm['since'])
"
```

---

## Summary line

End every run with one structured line:

```
supervisor: <ts> — PRs merged: <N>, failures triaged: <N>, auto-repaired: <N>, tickets created: <N>, escalated: <N>
```

This line is parsed by `nightbeat-report.py` (future extension) for the
morning summary.
