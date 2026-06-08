---
name: healthcheck
description: Repo healthcheck — git hygiene, test status, and deep freshness verification of status/directive docs. Gracefully degrades when project-specific conventions (git-erg tickets, STATE.md, etc.) are absent.
disable-model-invocation: false
user-invocable: true
argument-hint:
---

# Repo healthcheck

Run a healthcheck on the current repository. Report results concisely — one line per check, flag anything abnormal.

This skill is user-level and must **gracefully degrade**: each check runs only if its prerequisites are present. Missing prerequisites yield a `skip` status with a one-line reason, never a fail.

## Data collection

First, run the mechanical probe to collect structured state:

```bash
python3 ~/.claude/scripts/project-state.py "$(git rev-parse --show-toplevel)" --tests
```

Parse the JSON output. Use its fields to populate checks 1–10 below without re-running git commands — the probe covers everything through check 9; only check 10 requires additional file reads. If the script is missing or fails, fall back to ad-hoc commands per check.

## Checks

1. **Recent activity** — from `git.recent_commits`. List count and key themes.
2. **Open PRs** — from `prs.open` / `prs.items`. Skip if `prs.error`.
3. **Origin sync** — from `git.ahead` / `git.behind`. Skip if no remote. Also explicitly check local `main` vs `origin/main`:
   ```bash
   git rev-list --left-right --count main...origin/main
   ```
   Flag `warn` if local main is behind origin/main (needs pull) or ahead (unpushed commits on main).
4. **Branch hygiene** — from `branches.local` / `branches.remote` / `branches.details`. For each local branch:
   - **Non-ticket branches** with `commits_beyond_default > 0`: flag as cleanup candidate.
   - **Closed-ticket branches** (name matches `t<NNNN>-*` and ticket NNNN has a `Closed:` line) where the merge probe succeeds: classify as **fix-now** — safe to delete. Run this probe per branch:
     ```bash
     merge_base=$(git merge-base main <branch>)
     pr_num=$(grep -oP '^Closed:.*#\K[0-9]+' tickets/closed/$(ls tickets/closed/ | grep -P "^$(echo <branch> | grep -oP 't\K\d+')-" | head -1) 2>/dev/null | head -1 || true)
     [ -n "$pr_num" ] && git log $merge_base..main --format="%s%n%b" | grep -qE "\(#${pr_num}\)"
     ```
     If the probe exits 0, the branch landed on main. Emit one fix-now bullet per matching branch: `Delete local branch \`<branch>\` (closed ticket <NNNN>, merged into main)`.
     Note: for branches merged before 2026-05-25, the repo used squash-merge — `git merge-base --is-ancestor` is unreliable for those; the PR-number grep above handles both merge strategies.
   - **Closed-ticket branches** where the merge probe fails (grep exits non-zero): flag as cleanup candidate (commits not yet on default branch — manual review needed before deleting).
5. **Worktrees** — from `worktrees`. Flag entries with `locked: true` whose lock pid is no longer running. For each worktree, also run:
   ```bash
   git log <worktree-head>..<main-head> --oneline | wc -l
   ```
   If the count is > 0, flag as `warn`: "worktree `<name>` is N commits behind main — filesystem state (tickets/, docs/) may be stale relative to main".
6. **Working tree** — from `git.clean` / `git.dirty_files`. List uncommitted files if dirty.
7. **Tests green** — from `tests.status` / `tests.detail`. Skip if `tests.runner == "none"`.
8. **Housekeeping** — from `housekeeping.state` / `housekeeping.age_hours` / `housekeeping.branch`. Report `ok` if `state == "clean"` (age ≤ 12 h), `warn` if `state == "needed"` (overdue) or `state == "tidying"` (a `claude/housekeeping-*` branch is in flight). Skip if probe missing.
9. **Ticket archival** — from `tickets.closed_unarchived` (list of ticket IDs sitting in `tickets/*.erg` with a `Closed:` header, never moved to `tickets/closed/`). `ok` if empty; `warn` listing the IDs otherwise. This is the close-without-archive escape: a PR merged outside `erg-pr-merge` skips the `erg archive` step. Classify the fix as **fix-now** — `tickets/erg archive` (moves all closed tickets to `tickets/closed/`; commit the move). Skip if `tickets.error` is set or no `tickets/` directory.
10. **Docs freshness (deep verification)** — cross-check status/directive docs (`STATE.md`, `README.md`, etc.):
   - **Staleness** — flag docs whose content predates recent repo activity
   - **Ticket cross-check** — references to tickets whose status contradicts
     the doc (todo but closed, done but open, broken ref). Skip if no `.erg` tickets.
     (Use `tickets.ready_ids` for the initial ticket list; only read specific tickets
     whose status contradicts a doc reference.)
   - **PR cross-check** — PRs described as pending but already merged/closed.
     Use `prs.items` from the probe. Skip if `prs.error`.
   - **Count consistency** — "N open tickets" claims vs `tickets.open` from probe

## Output format

```
## Healthcheck — {date}

| Check            | Status | Detail                       |
|------------------|--------|------------------------------|
| Recent activity  | ...    | N commits (last 12h)         |
| Open PRs         | ...    | N open                       |
| Origin sync      | ...    | synced / ahead N / ...       |
| Branch hygiene   | ...    | N local, N remote            |
| Worktrees        | ...    | N active                     |
| Working tree     | ...    | clean / N changes            |
| Tests green      | ...    | N passed / K failed          |
| Housekeeping     | ...    | clean / needed / tidying     |
| Ticket archival  | ...    | N closed-but-unarchived      |
| Docs freshness   | ...    | N docs scanned, K stale refs |
```

Use `ok` for normal status, `warn` for attention-needed, `fail` for problems, `skip` for gracefully-degraded checks (detail column explains why).

If docs freshness is warn/fail, list each stale finding under the table as one bullet per finding, with the doc, line reference, and the fix (e.g., `STATE.md:39 — ticket 0095 listed as TODO but Status: closed (PR #259)`). This detail is the point of the deep check — do not compress it into a single line.

After the table (and any stale-findings list), add a one-line summary verdict.

## Action plan

After the verdict, if any findings are warn or fail, emit an **Action plan** section.
Classify every finding into exactly one of three categories:

- `fix-now` — trivial, no branch needed, reversible, no design decision: do it in the
  current session immediately after the user says "do it"
- `open-ticket` — multi-file, needs a branch, requires a design decision, or worth
  tracking across sessions: create a ticket
- `skip` — cosmetic, already tracked elsewhere, or not worth acting on now: note why

Format:

```
## Action plan

**fix-now**
- {one-line description of fix}

**open-ticket**
- {title} — {one-line reason it needs a ticket}

**skip**
- {finding} — {reason}
```

Omit a heading if it has no entries. If all checks are `ok`, omit the Action plan entirely.

> **Contract** — `/molt` parses this section programmatically. The bold headings `**fix-now**`, `**open-ticket**`, `**skip**` are a stable interface; do not rename or reformat them.

Once the Action plan is fully effected, propose: "Surface remaining nits?"
