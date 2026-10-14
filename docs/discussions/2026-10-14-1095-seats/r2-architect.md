# R2, lead architect (KISS): revised options for ticket 1095

Inputs: r1-portability (gpt-6.1-sol), r1-evidence and its census, r1-values (simulated), and probe-result.txt. The probe ran on git 2.43.0: an `.tmp/` listed in info/exclude is invisible to `status --porcelain --untracked-files=all`, shows only with `--ignored`, and plain `git worktree remove` deletes it with exit 0.

## What round 1 got wrong (accepted)

1. **The purge-list idea was unsafe.**
   - `worktree-gc.sh` (lines 136-155) and `worktree-exit-preflight.sh` (lines 41-52) both delete `.panel/` and `build/panel-head/` *before* the WIP check.
   - Adding `.tmp/` there would delete it even when other WIP then blocks removal.
   - My claim that `.tmp/` "inherits the WIP rail" was false: an excluded path is invisible to that rail.
2. **"Moving to disk removes Disk full" was overstated.**
   - /home is 92% used with 84G free, against 17G free on /tmp.
   - Moving bytes changes which filesystem fills; it does not prevent a fill.
3. **The documented outages are doudou project-test leaks**, which my round-1 options do not touch:
   - the 2026-09-06 `zoteus-*` leak from vitest in the zotero repository;
   - `glossary-0882-*`, 85 directories on padme and many on doudou.
   - The padme 11.9G is a different and episodic phenomenon: two climate-finance-het audit tasks, three days after a reboot.
4. **The t2093 audit JSONs (1.6-2.1G single files) are probably deliverable evidence, not scratch.** "Evidence is by definition not in .tmp/" is a definition, not a mechanism.
5. **Bare-/tmp ownership is a naming convention only** (`tNNNN-*`, 135 entries). Nothing machine-checkable ties such an entry to an owner.

Option B is dropped:
- It brings back age-based deletion, which the constraint forbids.
- It duplicates the liveness logic.
- It cannot see doudou or remote sessions.
- Its one unique merit, covering sessions with no worktree, is better served by a report (Option 1).

Two options remain. They nest: Option 2 is Option 1 plus one rule.

## Option 1: observability only ("see it, then decide"), revised from C

**Mechanism.** A report-only scan, `scripts/tmp_report.py`, extending the existing `session_scratch.scan()` that feeds healthcheck item 12. It covers:
- **Roots:** `${TMPDIR:-/tmp}`, the runtime temp root, `~/.cache` (where the STATE-line-31 idiom sends test temps), and the `.tmp/` of every registered worktree of the current repository.
- **Grouping:** entries are grouped by name pattern, with size, owner, mtime and count. Patterns:
  - `t<N>-*` and `<repo>-t<N>-*`
  - known runtime roots (`claude-<uid>`, `pi-bash-*`, `pytest-of-*`)
  - "other repeated stem": any stem with more than k siblings, such as `glossary-0882-*`, `zoteus-*`, `uv-N.lock`. This is the project-test-leak detector.
- **Honesty:** it reports filesystem use for both `/tmp` and `/home`, and it prints `could not read N entries` rather than letting them drop out (values seat).
- **When it runs:** at healthcheck and at molt, on each host where molt runs. Doudou is covered when molt runs there.
- **Deletion:** none.
- **Routing what it finds:**
  - A leaking stem is named in the report as a project-test leak. Below the severity floor, nobody files a ticket; the project fixes it with per-command `TMPDIR`.
  - A `t<N>-*` entry is listed under "owner ticket N, repo unknown". Resolving the repository is the reader's job, because names do not prove ownership.

**Lifecycle points:**
- At command or test completion: none (that stays project hygiene).
- At roar: none.
- At molt: report only.
- Crash recovery: by hand, informed by the report. A reboot remains a recovery on tmpfs hosts, and the author knows it destroys evidence.

**Answers:** the observability companion; the doudou focus (stems detect zoteus- and glossary-style leaks); the /home transfer risk (both filesystems are shown); the risk of silent unreadable entries.

**Accepts as residual:**
- The author still deletes by hand.
- Nothing runs once Bash is already dead (the 2026-09-06 mode).
- It does not prevent the next fill; it only shortens the time to diagnosis. The census shows a top-N would have named t2093 and t2094 on 12 Oct.

**Deletes or replaces:** it subsumes healthcheck item 12's scan into one report. `session_scratch.py --sweep` and on-end.sh stay unchanged.

**Verification:**
- Fixture roots under pytest `tmp_path`, run serially.
- Positive controls:
  - a planted `t9999-x` directory is listed under ticket 9999;
  - 12 planted `leak-*` siblings are reported as a repeated stem;
  - a mode-000 entry increments "could not read";
  - a `.tmp/` in a fixture worktree is counted.
- A null report on the real host counts only after those controls pass.

**Price:** 2-3 agent-hours, 0.5 author-hour, about $25-45. (Derived: about $12-15 per agent-hour.)

## Option 2: worktree-owned `.tmp/`, removed only with its worktree, plus Option 1 (revised from A)

**Delta from round 1:** no purge list, no pre-WIP deletion, and no change to `worktree-gc.sh` or `worktree-exit-preflight.sh` deletion code. The worktree's own removal is the only thing that deletes `.tmp/`. The probe shows plain `git worktree remove` already does that, and it runs only after every rail has passed: live cwd, live lock, real WIP, and upstream gone or ancestry.

**Contract (one rule in `rules/workflow.md`, one line in hunt):**
- `<worktree>/.tmp/` is **declared disposable**: logs, caches, virtual environments, test basetemps (via per-command `TMPDIR=<worktree>/.tmp`, never session-wide, because of the 108-byte socket path limit).
- **Evidence never goes there.** Deliverable or review evidence goes where the project keeps evidence: committed, DVC-tracked, or attached to the PR. That would have been the right home for the t2093 audit JSONs.
- hunt appends `/.tmp/` to the common `info/exclude` and says so.
- Read-only seats (Codex read-only, reviewers) do not write and need nothing.
- No-worktree sessions: Claude uses its own scratchpad; other runtimes use `<primary>/.tmp/`, which no lifecycle removes and Option 1 reports.

**Lifecycle points:**
- **Command or test completion:** unchanged; `mktemp` plus trap, or `tmp_path`, is the author's job.
- **Roar:** preflight gains a *report*, not a deletion. It lists `.tmp/` via `git status --ignored --porcelain -- .tmp`, prints `.tmp/: N files, X MB will go with the worktree`, and asks the agent to confirm nothing in it is cited by a verdict or PR. This is the values seat's "promote, then remove", as a reading step. Removal then happens through the existing path (ExitWorktree, or plain `git worktree remove` on Codex and Pi; ExitWorktree is a convenience, not the basis).
- **Crash recovery (molt):** `worktree-gc.sh` prints the same size line *before* the `worktree remove` it already performs. A tree that is crashed but unmerged keeps its `.tmp/` indefinitely. That is safe but unbounded, and Option 1 makes it visible.

**Answers:**
- Purge-before-WIP ordering: there is no purge; WIP blocks the whole removal, `.tmp/` included.
- Silent evidence loss: the size line plus the evidence-goes-elsewhere rule.
- Ownership by name only: inside worktrees, ownership is git registration, not a name.
- Portability: plain git and paths, with no hook or runtime ID as the basis. Hooks may remind.
- Observability: it ships with Option 1, not "later".

**Accepts as residual:**
1. **Disk transfer.** Bytes move from tmpfs (17G free, where a fill kills every session's Bash silently) to /home (84G free, backed up by restic). A fill there is louder and slower but worse when it happens. This is a choice of failure mode, not a removal of risk, and Option 1 watches both. A restic exclude for `.tmp/` should be checked; that is a small item.
2. **Habit.** Agents may keep writing to bare `/tmp`; the rule only works if it is followed, and Option 1 is the check.
3. **Pi's own `pi-bash-*.log` files** come from the parent process via `os.tmpdir()`, so per-command `TMPDIR` cannot reach them. They are 2.3M; an adapter could handle them.
4. **`[gone]` is not proof of merge, and gc reads only `/proc/*/cwd`.** These rails already exist and this option does not change them; it does not make them weaker either.
5. **Project test leaks** (zoteus, glossary) are unchanged. They are named by Option 1 and fixed in their own projects.
6. **Gigabyte files inside a tree may slow `rg` and status scans.** This is an inference; ignored paths are skipped by `rg` by default.

**Verification (serial, throwaway repositories under `tmp_path`):**
- **Ordering control:** real WIP plus `.tmp/x` leads to gc skipping and preflight blocking, and `.tmp/x` still exists. This test fails if anyone later adds `.tmp` to a pre-WIP purge.
- Clean, gone tree with `.tmp/` is removed, and the size line is printed.
- Live cwd: kept.
- A tracked file under `.tmp/` shows as WIP: kept.
- No exclude: `.tmp/` shows as untracked WIP: kept (fail-safe).
- The probe already supplies the positive control for remove-deletes-ignored on git 2.43; pin the minimum git version in the test.
- Plus all of Option 1's tests.

**Deletes or replaces:** no code is deleted. It retires the ad-hoc `/tmp/tNNNN-*` habit, which was 74% of padme's /tmp today. It adds about 20 lines across preflight and gc, all report-only.

**Price:** 5-7 agent-hours, 1 author-hour (decision plus review), about $60-100. Option 1 accounts for 2-3 of those agent-hours.

## Demonstrated versus speculative

| Need | Status |
|---|---|
| See what fills /tmp, per host, by owner pattern | demonstrated (t2093/t2094; the 09-16 git-erg review; doudou glossary leftovers) |
| Prevent project-test leaks | demonstrated, but owned by projects; the harness only names them |
| A task-owned place for ad-hoc temporaries | demonstrated on padme (74%); on doudou not yet measured as an outage cause |
| A liveness-aware sweep of bare /tmp | speculative: no incident, and no age-free owner signal |
| tmpfs speed for task caches | speculative, never measured |

## Out of scope, for the author

- The 11.9G in `/tmp/t2093-*` and `/tmp/t2094-*` belongs to climate-finance-het. That project's session decides whether a verdict cites the audit JSONs, then archives or deletes them. The harness does not sweep it.
- Doudou's quota is the documented outage site. A run of Option 1 there is a cheap measurement to make before choosing between the two options.
