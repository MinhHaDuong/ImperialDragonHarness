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

**Commit tracked writes immediately.** Every write to a tracked file in
`$HARNESS_DIR` (`settings.json`, `scripts/beat.py`, `tickets/*.erg`) must be <!-- harness-extension-point -->
followed by `git add <file> && git commit -m 'chore(supervisor): <description>'`
before proceeding to the next action. Uncommitted tracked files cause the next
beat cycle's dirty-tree pre-flight to abort.

## 1. Survey

Pre-flight: verify no dual-journal state exists (`canonical` vs `logs/` path). If both
`<project>/nightbeat-supervisor-journal.jsonl` and `<project>/logs/nightbeat-supervisor-journal.jsonl`
exist as independent files (not a symlink), stop and open a ticket before proceeding.
The survey script enforces this automatically and exits non-zero if the condition is detected.

```bash
python3 $HARNESS_DIR/scripts/nightbeat-supervisor-survey.py [--since ISO-TS]
```

If `--since` is absent from `$ARGUMENTS`, the script derives the watermark from
the latest `ts` in `$HARNESS_DIR/nightbeat-supervisor-journal.jsonl` (defaults
to 24h ago if no journal exists). Reads `$HARNESS_DIR/logs/beat-outcomes.jsonl`
and finds open PRs for raid-success tickets via remote branch lookup and forge API.
Outputs `{prs_to_merge, failures, watermark_ts, journal_context}`.
If both lists are empty, write a journal `action=idle` entry and stop.

## 2. Merge ready PRs

For each entry in `prs_to_merge` (which includes `pr_number`, `github_repo`,
and `project_path` derived by the survey script from the project's git remote):

1. `bash $HARNESS_DIR/skills/nightbeat-supervisor/check-pr-diff <pr_number> <github_repo>` — non-zero exit is a HOLD; add to failures with the script's reason.
2. Switch to the target project and check out the PR branch:
   ```bash
   cd <project_path>
   git fetch origin
   gh pr checkout <pr_number> --repo <github_repo>   # harness-extension-point
   ```
   Then: `/verify-gate <pr_number>` — APPROVED → `/merge <pr_number>`. REROLL → append the failing criteria as a note on the linked ticket (create the ticket if none is referenced in the PR body), then commit the ticket file:
   ```bash
   cd $HARNESS_DIR
   git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): append REROLL note to <ticket>'
   ```
   and move on. ESCALATE → go to step 4.
   After verify-gate and merge complete, `cd $HARNESS_DIR` to return to the harness directory for the next PR.

## 3. Diagnose and repair

For each failure, read the nightbeat log and ask **why** until you reach an
actionable root cause:

> Why did it fail? → Why did that happen? → Why was that condition present?

When you reach a root cause, repair if within authority:

- **Missing permission** → add to `settings.json` allowlist, then
  `git add settings.json && git commit -m 'chore(supervisor): add <permission> to allowlist'`.
- **Budget too small for the actual scope of work** → before raising, apply
  the convergence guard:
  1. Count `action=repair` journal entries for the same project+phase in the
     last 7 days. If ≥ 3: **do not raise**. Instead, open a ticket:
     "budget not converging for {project} {phase} — {N} raises in 7 days,
     current={current}, started={first}."
     Then `git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): convergence ticket for <project>'`.
  2. If the proposed raise would exceed 1.5× the module-level constant for
     that phase, log a warning and include it in the ticket body (note: the
     hard ceiling remains 2× the module-level constant — the 1.5× threshold
     is a warning only, not a new cap).
  If neither guard triggers: raise the per-project `ProjectConfig` field in
  `beat.py` by 20%, capped at 2× the module-level constant; never touch the
  module-level constant. Then
  `git add scripts/beat.py && git commit -m 'chore(supervisor): raise <field> budget for <project>'`. <!-- harness-extension-point -->
- **Raid timeout during verify/review** (`outcome=timeout` AND why-chain
  shows verify/review slowness, not implementation slowness) → raise
  `raid_timeout_s` in the per-project config by 20%, capped at
  2× `RAID_TIMEOUT_S` (3600 s). Then
  `git add scripts/beat.py && git commit -m 'chore(supervisor): raise raid_timeout_s for <project>'`. <!-- harness-extension-point -->
  Implementation slowness is a "ticket too
  large" signal — do not raise the timeout for that.
- **Ticket too large to finish in one beat** → split into one ticket per
  independent unit of work; leave the parent open as an umbrella. Each child
  ticket must carry `Blocked-by: <umbrella-id>` so pick-ticket can auto-close
  the umbrella when all children are done (it uses inverse lookup, not a
  `Blocks:` header — that header is not valid in %erg v1). Commit the new
  ticket files by naming each child (`git add tickets/<child-id>-*.erg`, one per
  child), then `git commit -m 'chore(supervisor): split <ticket> into children'`
  — never `git add` over the whole `tickets/` glob, which also sweeps a stray
  `.erg` left by another agent in the shared checkout.
- **Dead timer** → restart it.
- **Dirty working tree** (`outcome=aborted-dirty-tree`) → if the dirty files
  are machine-local state (beat-outcomes.jsonl, STATE.md, build artifacts),
  commit or stash them; otherwise open a ticket naming the dirty files and
  their likely source, and `git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): dirty-tree ticket'`.

If the why-chain bottoms out without reaching anything repairable: escalate
(step 4).

**Anything else**: open a ticket stating the root cause chain; do not
auto-repair. Then `git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): ticket for <root-cause>'`.

## 4. Escalate

Triggers: ESCALATE from verify-gate, why-chain without a repairable finding,
or the same root cause recurring ≥ 3 consecutive runs for a project.

Call `advisor` if available. Otherwise `Agent(model="opus")` with the log
context (no extended thinking in Agent mode — honest degradation). Create a
ticket with the verdict if the fix is outside authority. Commit the ticket:
`git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): escalation ticket for <project>'`.

## 5. Done

Append one journal entry per action taken this cycle to
`$HARNESS_DIR/nightbeat-supervisor-journal.jsonl`. If no actions were taken,
append a single `action=idle` entry — this serves as the watermark so the
next cycle knows where to resume.

**Clean-tree guard.** Before printing the summary, run:
```bash
cd $HARNESS_DIR
dirty=$(git status --porcelain)
if [ -n "$dirty" ]; then
  echo "WARNING: supervisor leaving dirty tree: $dirty"
  git add -u && git commit -m 'chore(supervisor): commit residual tracked writes'
fi
```
This is a safety net — every write should already be committed by the steps
above. If the guard fires, it means a write point was missed; log the warning
so the next nightbeat-report flags it for a skill fix.

End with:

```
supervisor: <ts> — merged: N, repaired: N, tickets: N, escalated: N
```
