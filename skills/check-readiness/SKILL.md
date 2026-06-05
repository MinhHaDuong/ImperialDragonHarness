---
name: check-readiness
description: Multi-repo pre-flight readiness check and interactive triage. Surfaces git hygiene, ticket health, configuration drift, and nightbeat risk signals.
user-invocable: true
argument-hint: "[--mode {default|nightbeat-history}] [--project <name>] [--hours N]"
---

# Check Readiness — multi-project pre-flight

Run this skill before starting autonomous work across the harness to audit global
configuration health, project readiness, and surface risk signals from prior runs.

**Three modes:**

- **default** (full sweep): Audit all projects in `~/.claude/projects.json` for:
  - Per-repo git hygiene (uncommitted, drift from origin, stale branches, dirty worktrees)
  - Ticket flow health (open count, stale-claim count, unclaimed ready, blocked-by chains)
  - CLAUDE.md presence and freshness
  - `.claude/settings.json` drift across projects (skill aliases, permission allowlists, hooks)
  - Aggregate signals across the fleet

- **--mode=nightbeat-history**: Legacy behavior — de-risk one autonomous nightbeat
  by scanning the prior journal for risky-ticket signals (parallel-fanout cost,
  repeated picks, permission denials). Use this before scheduling `nightbeat-supervisor`.

- **--project <name>**: Scope to one project. The project name is the base name
  from `~/.claude/projects/<name>`. Runs full audit on that project only.

## Implementation steps

### Mode: default (multi-repo full sweep)

1. **Resolve erg binary**
   ```bash
   ERG=$(command -v erg 2>/dev/null || echo "tickets/erg")
   ```

2. **Load projects list**
   Load `~/.claude/scripts/projects.json` and iterate over each `path` entry.
   Expand `~` to `$HOME`. For each project:

   a. **Git hygiene check**
      - Check for uncommitted changes: `git status --porcelain`
      - Check for drift from origin: `git rev-list --count origin/main..HEAD` (commits not pushed)
      - List stale branches: `git branch --list --no-merged origin/main` (older than 7 days)
      - Check for dirty worktrees: `git worktree list` if a main repo

   b. **Ticket flow health** (if `tickets/` exists)
      - Open ticket count: `erg status tickets/ | wc -l`
      - Ready ticket count: `erg ready tickets/ | wc -l`
      - Stale-claim count (claimed but no activity in 14 days)
      - Blocked-by chains of depth ≥ 3

   c. **Configuration audit**
      - CLAUDE.md exists and last-modified date
      - .claude/settings.json exists; check for permission drift vs. global settings.json
      - Skill library location and versions if per-project skills exist

3. **Aggregate and present**
   Generate a summary table:
   ```
   | Project | Status | Git | Tickets | Config | Notes |
   |---------|--------|-----|---------|--------|-------|
   ```

   For each project, use status indicators:
   - **Git**: clean / ⚠ uncommitted / ⚠ drift / ⚠ stale
   - **Tickets**: open/ready ratio; any blocked chains?
   - **Config**: consistent / ⚠ drift

4. **Interactive triage**
   For each project flagged with issues (≥ 1 ⚠ indicator):
   Present the findings and offer:
   a. **commit**: Stage and commit any changes (git add -u && git commit)
   b. **branch**: Create a new branch for the changes
   c. **note**: Record an explanation without committing
   d. **skip**: Leave unchanged, move to next

5. **Housekeeping**
   After triage, present a summary of changes across all projects.

---

### Mode: --mode=nightbeat-history (legacy single-repo risk review)

This mode preserves the original `nightbeat-risk-review` behavior for backward
compatibility until ticket 0068 (alias system) is closed.

1. **Resolve erg binary**
   ```bash
   ERG=$(command -v erg 2>/dev/null || echo "tickets/erg")
   ```

2. **Collect the raw report** (current repo only)
   Run:
   ```bash
   python3 ~/.claude/scripts/nightbeat-report.py --full --hours 72
   ```
   Accept `--hours N` from the skill argument and substitute it (default: 72 = 3 nights).
   Capture and read the full output.

3. **Extract risk signals**
   For each run in the report, read the ticket ID from the **Ticket** column of the run table
   (the four-digit number shown for runs where a ticket was picked; rows showing `—` had no pick).
   Flag a ticket if **any** of:
   - `total_cost_usd > 2.0` — parallel fanout risk
   - `stop_reason` is `None` or absent — budget kill or crash
   - Same ticket ID picked ≥ 2 times in the window with no new commits between picks — repeated pick, no progress
   - Result text contains "Access Denied" or "permission denial"
   - `num_turns < 5` and `total_cost_usd > 1.0` — expensive but fast, parallel agents died early

4. **Present risk table**
   Display a ranked table (worst signals first):
   ```
   | Ticket | Project | Attempts | Max Cost ($) | Signals |
   |--------|---------|----------|--------------|---------|
   ```

   If no tickets are flagged, print "No risk signals detected in the window." and stop.

5. **Interactive triage**
   For each flagged ticket (in risk-rank order), present signals and offer:

   a. **sweep-skip** — tag the ticket deferred:
      ```bash
      $ERG tag NNNN deferred tickets/
      $ERG log NNNN "claude note sweep-skip: <signal>, deferred after risk review" tickets/
      ```
      Replace `<signal>` with the actual risk signal (e.g. `cost>$2`, `budget-kill`, `repeated-pick`, `access-denied`, `expensive-fast`).

   b. **note** — append an explanation without tagging:
      ```bash
      $ERG log NNNN "claude note <reason>" tickets/
      ```

   c. **open sub-ticket** — split into a smaller ticket: invoke `/ticket-new` to create the sub-ticket with a focused scope.

   d. **skip** — leave unchanged, move to next.

   Record every action taken.

6. **Housekeeping commit**
   After triage, commit all modified ticket files (`-u` stages tracked
   edits only — a stray `.erg` left in `tickets/` is never swept in):
   ```bash
   git add -u tickets/
   git commit -m "chore(tickets): nightbeat risk-review triage $(date +%Y-%m-%d)"
   ```
   If no files were changed (all `skip`), print "No changes to commit."

---

### Mode: --project <name> (single-project scope)

Identical to **default mode**, but iterate over only the named project.
The project name is the base name from `~/.claude/projects/<name>`.

Example: `check-readiness --project my-project` runs the full audit on
that project only (resolves to `<path>` from `projects.json` entry).

---

## Arguments

- `--mode {default|nightbeat-history}`: Select sweep mode. Default: `default`.
- `--project <name>`: Scope to one project (base name from `~/.claude/projects/`).
  If specified, implies full audit (ignores `--mode` unless `--mode=nightbeat-history`).
- `--hours N`: For nightbeat-history mode, number of hours to scan in the journal.
  Default: 72 (3 nights).

---

## Backward compatibility

The old `nightbeat-risk-review` skill is preserved as `/check-readiness --mode=nightbeat-history`
for compatibility until ticket 0068 (alias system) is closed. After 0068 closes, a shell
alias or skill redirect can be configured.
