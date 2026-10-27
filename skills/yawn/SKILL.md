---
metadata:
  category: session
name: yawn
description: "Repo healthcheck, reports first, fixes on request: git hygiene, test status, doc freshness; degrades without project conventions. Not for unprompted fixes (/molt)."
disable-model-invocation: false
user-invocable: true
argument-hint:
---

Bounded, mostly mechanical audit work; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Yawn — repository healthcheck

Neighbouring skills and when to prefer each: [session-lifecycle](../lair/references/session-lifecycle.md).

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Run a healthcheck on the current repository. Report results concisely — one line per check, flag anything abnormal.

This skill is user-level and must **gracefully degrade**: each check runs only if its prerequisites are present. Missing prerequisites yield a `skip` status with a one-line reason, never a fail.

## Data collection

First, run the mechanical probe to collect structured state:

```bash
python3 "$IDH_ROOT/scripts/project-state.py" "$(git rev-parse --show-toplevel)" --tests
```

Parse the JSON output. Use its fields to populate checks 1–12 below without re-running git commands — the probe covers everything through check 10 and checks 12–13; only check 11 requires additional file reads. If the script is missing or fails, fall back to ad-hoc commands per check.

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
     bash "$IDH_ROOT/skills/molt/ticket-sweep.sh" merged-probe <branch>
     ```
     Exit 0 means the branch landed on main: ancestry (`git merge-base --is-ancestor`) or, as an equal second signal, the merge request number from the ticket's `Closed:` header appearing as `(#N)` in a subject on main. Emit one fix-now bullet per matching branch: `Delete local branch \`<branch>\` (closed ticket <NNNN>, merged into main)`.
     Note: the merge-request-subject signal stays because ancestry misses squash merges in the past, which left no ancestry; the probe tries both.
   - **Closed-ticket branches** where the merge probe exits 1 (not merged) or 2 (`could-not-determine`: the branch maps to no ticket or the ticket records no merge request number, or `tickets/` or erg is missing): flag as cleanup candidate for manual review, not fix-now. Exit 2 is never a deletion.
5. **Worktrees** — from `worktrees`. Flag entries with `locked: true` whose lock pid is no longer running, and those whose lock has no checkable pid (none, pid 1, several, or past pid_max): `worktree-gc` reclaims the harness shapes (`(pid 1`, `(owner pid not visible)`) on a clean tree idle 72 h (`skills/hunt/references/worktree-lifecycle.md`) and never the others, which are manual-removal candidates once their session is over. For each worktree, also run:
   ```bash
   git rev-list --count <worktree-head>..<main-head>
   ```
   If the count is > 0, flag as `warn`: "worktree `<name>` is N commits behind main — filesystem state (tickets/, docs/) may be stale relative to main".
6. **Working tree** — from `git.clean` / `git.dirty_files`. List uncommitted files if dirty.
7. **Tests green** — from `tests.status` / `tests.detail`. Skip if `tests.runner == "none"`.
8. **Housekeeping** — from `housekeeping.state` / `housekeeping.age_hours` / `housekeeping.branch`. Report `ok` if `state == "clean"` (age ≤ 12 h), `warn` if `state == "needed"` (overdue) or `state == "tidying"` (a `claude/housekeeping-*` branch is in flight). Skip if probe missing.
9. **Ticket archival** — from `tickets.closed_unarchived` (list of ticket IDs sitting in `tickets/*.erg` with a `Closed:` header, never moved to `tickets/closed/`). `ok` if empty; `warn` listing the IDs otherwise. This is the close-without-archive escape: a merge that skipped the merge recipe's close step skips `erg archive`. Classify the fix as **fix-now** — `bash "$IDH_ROOT/skills/molt/ticket-sweep.sh" archive` (moves all closed tickets to `tickets/closed/` and stages the move; commit it). Skip if `tickets.error` is set or no `tickets/` directory.
10. **Hook freshness** — from `hooks`. Skip (silent) if `hooks.hooks_path` is null or `hooks.in_worktree` is false — no working-tree `core.hooksPath`, so the stale-hook-in-worktree trap does not exist. `skip` with the reason if `hooks.error` is set (no remote, detached HEAD). `warn` if `hooks.stale_files` is non-empty, naming the files: "working-tree hooks differ from origin/<default> — worktrees will run the main checkout's stale hooks until it is updated". `ok` if in-worktree hooks match the default branch. Advisory only, never a hard gate.
11. **Docs freshness (deep verification)** — cross-check status/directive docs (`STATE.md`, `README.md`, etc.):
   - **Staleness** — flag docs whose content predates recent repo activity
   - **Ticket cross-check** — references to tickets whose status contradicts
     the doc (todo but closed, done but open, broken ref). Skip if no `.erg` tickets.
     (Use `tickets.ready_ids` for the initial ticket list; only read specific tickets
     whose status contradicts a doc reference.)
   - **PR cross-check** — PRs described as pending but already merged/closed.
     Use `prs.items` from the probe. Skip if `prs.error`.
   - **Stored counts** — STATE.md stores no derived number (rules/state.md):
     a legacy generated `## Status` block is a `warn`, fixed by replacing it
     with the pointer line. Ticket counts are not compared: there are none.
   - **Stale forward promises** — resident skill and rule bodies are directive
     docs too. Grep `skills/*/SKILL.md` and `rules/` for `until the`, `not yet
     drafted`, `when converted`, `for now`, then confront each promise with the
     decision behind it: a study voided, a ticket closed wontfix, work never
     scheduled. Such text reads as pending work and agents act on it — a flag
     from a cancelled A/B was still being recommended as a live
     cost lever two months later. Judgment call, deliberately
     unguarded: report the stale ones, never auto-edit.
12. **Session scratch (host-level)** — from `session_scratch`. The one check
    that is not about this repo: every session gets a scratch directory under
    the user's temp root, one per distinct cwd it visits, and nothing but the
    `SessionEnd` hook removes one. `skip` (silent) if `session_scratch.exists`
    is false. `warn` when `session_scratch.status` is `warn`, quoting
    `session_scratch.reasons`:
    - **Usage** — `root_bytes` against `cap_bytes`. Read `cap_source` before
      quoting the percentage: where the temp root is a quota-enabled tmpfs the
      cap is *inferred* from the init system's default per-user share, because
      the quota tools cannot read a tmpfs quota. Say "inferred cap", never
      "quota reads". A fill here is not cosmetic. It kills the Bash tool with
      EDQUOT in every session of that user at once.
    - **Truncation** — read `session_scratch.truncated` before quoting any byte
      figure. When it is true the directory walk stopped at its entry ceiling,
      so `root_bytes` and `orphan_bytes` are a floor rather than a total; the
      probe says so in `reasons` and its status is `warn`, never `ok`.
    - **Orphans** — `orphan_count` / `orphan_bytes`, session directories no live
      process owns (no open descriptor inside them, no process cwd'd there, and
      the id named by nothing running). Classify as **fix-now**: `Sweep N orphan
      session scratch directories (X reclaimable)`. /molt applies it.
    - In the warning, name the relocation knob but do not set it: moving the
      temp root is an operator decision, since the root must also stay short —
      sandbox socket paths are built under it. The runtime knob is
      <!-- harness-extension-point -->
      `CLAUDE_CODE_TMPDIR`, which takes precedence over `TMPDIR`.

## Output format

```
## Yawn — {date}

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
| Hook freshness   | ...    | in sync / N stale / skip     |
| Docs freshness   | ...    | N docs scanned, K stale refs |
| Session scratch  | ...    | N orphan dirs, X of cap      |
| Local directives | ...    | N shadow / N reasoned / skip |
```

Use `ok` for normal status, `warn` for attention-needed, `fail` for problems, `skip` for gracefully-degraded checks (detail column explains why).

If docs freshness is warn/fail, list each stale finding under the table as one bullet per finding, with the doc, line reference, and the fix (e.g., `STATE.md:39 — a ticket listed as TODO but Status: closed`). This detail is the point of the deep check — do not compress it into a single line.

After the table (and any stale-findings list), add a one-line summary verdict.

## Action plan

After the verdict, if any findings are warn or fail, emit an **Action plan** section.
Classify every finding into exactly one of three categories:

- `fix-now` — trivial, no ticket needed, reversible, no design decision: do it in the
  current session, on a branch, immediately after the user says "do it"
- `open-ticket` — multi-file, requires a design decision, or worth
  tracking across sessions: create a ticket. Apply the severity floor (`rules/workflow.md` § Autonomous action), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.
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

Last line of the report, only when the Action plan holds at least one `fix-now`
or `open-ticket` entry (a `skip`-only plan gets none), outside the headings above:

```
Next move: `/molt` effects the fix-now entries and files tickets for the open-ticket entries.
```

An all-ok run emits no Action plan and no suggestion.

Once the Action plan is fully effected, propose: "Surface remaining nits?"

13. **Disk headroom at session start** — from `disk_space`. Warn if either
    `/tmp` or `/home` has less than 10% free, naming the mount and reported
    percentage. A missing/unreadable mount is unknown, not healthy. This is an
    advisory warning; it never blocks startup.
14. **Local directives versus the harness** — the project's own `CLAUDE.md`,
    `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/rules/`, runtime skill roots and
    top-level `skills/` against the loaded harness rules and skills; never the
    harness against itself. Reporter only: no fixes, no tickets.
    ```bash
    python3 "$IDH_ROOT/scripts/project_shadow.py" "$(git rev-parse --show-toplevel)"
    ```
    The script prints JSON lines. A line with `status: skip` makes the check
    `skip` with its reason (the harness itself, or no local directives). Each
    other line is a name-collision finding (`kind` shadowing) carrying the local
    file, the harness file and the governing harness `instruction`; its
    `verdict` is `ok` when the reason is stated in place, shown as
    `ok (reasoned)`, and `warn` when the override is silent. Then the judged
    pass, which the script cannot do: read skill and rule *descriptions* first
    and open a full body only where descriptions overlap, to find
    - **contradiction** — a local instruction inverting a harness instruction;
    - **shadowing** by responsibility — a local skill or rule taking over a
      harness skill's job under another name;
    - **repeat** — a local copy of a harness procedure.

    Each judged finding uses the same record: kind, local file, harness file,
    governing instruction, verdict, and a proposed disposition (`delete-local`,
    `annotate`, `harness-ticket`) with its destination (project or harness).
    A local override that states its reason in place is `ok (reasoned)` (arena's
    `CLAUDE.md` replaces merge-by-PR with `git merge --no-ff` because the repo
    has no forge); a silent override or a copy is `warn`. `ok (reasoned)` never
    enters the Action plan.
