# R1, lead architect (KISS): tmp lifecycle for ticket 1095

## 1. What fills /tmp (padme, 2026-10-14, read-only; nothing deleted)

`/tmp` is a 32G tmpfs, 16G used (48%). There are 1001 top-level entries: 984 belong to `haduong` and every one of them dates from October; 17 belong to root (systemd, X11).

| Consumer | Size | Owner of the leak |
|---|---|---|
| `/tmp/t2094-switch` (`all/`, `withdrawn/`, `admission/` and logs, adherence yaml) | 5.8G | ad-hoc task evidence dir, 12 Oct |
| `/tmp/t2093-historical-audit` (audit.py, json, logs) | 5.3G | ad-hoc task evidence dir, 12 Oct |
| about 20 `numba-cache-*`, `nbc-*`, `nc1372_*`, `nb1372` | about 1.5G | ad-hoc experiment caches |
| `arena-uv-cache`, `pkgvenv`, `projenv`, `probe-venv` | about 0.6G | ad-hoc venvs and caches |
| `cr0673`, `clean0673`, `pre0673`, `strata-*`, `t2092-*` | about 0.5G | ad-hoc task dirs |
| `/tmp/claude-1000` (runtime session scratch) | 236M | already handled (0854) |
| `/tmp/pytest-of-haduong` (5 basetemps) | 179M | pytest, rotates itself |
| about 900 loose files (`uv-N.lock`, `race-N-N.err`, `tN-*.log`, `tN-pr-body.md`, `pi-bash-N.log`, …) | small | ad-hoc |

**Demonstrated:**
- Two ticket-named dirs that agents made themselves hold about 11G, roughly 70% of usage.
- The ad-hoc dirs as a group hold more than 95% of usage.
- The harness's own runtime scratch, which 0854 already cleans, is about 1.5%.
- `pi-bash-*.log` shows that non-Claude runtimes write to bare `/tmp`.
- The harness skills themselves almost never name `/tmp` (grep: three hits, two of them `mktemp`).

So the leak is in agent behaviour, not in harness code.

**Inference:**
- t2093 and t2094 belong to a project repository, not to the harness: harness ticket numbers are near 1100.
- `/tmp` is tmpfs, so a reboot is already a full crash recovery for padme. The leak only accumulates between reboots.
- doudou's case ("parallel pytest exhausts /tmp quota; set TMPDIR under ~/.cache", JETP-observer STATE line 31) is a project-test leak. The project has already fixed it locally.

**Speculative (no evidence yet):** a need for a cross-runtime registry, a temp-root daemon, or a startup sweep of arbitrary `/tmp` content. Nothing observed requires a liveness-aware sweep beyond the one `session_scratch.py` already has.

## 2. The real need

Every task temporary must have one owner and sit at a location the existing lifecycle already removes. The current situation:
- Worktrees already have a complete lifecycle: hunt creates them; roar's clean gate and `ExitWorktree remove` end them; `worktree-gc.sh` recovers them after a crash, with live, lock and WIP rails.
- Runtime session scratch already has one too (on-end.sh plus the `session_scratch.py --sweep` in molt).

What has no lifecycle is the third category: "a dir I made for this ticket". Option A gives that category to the first mechanism instead of building a fourth one.

## Option A (recommended): task temporaries live in the worktree, under `.tmp/`

**Mechanism:**
- **Rule:** one sentence in `rules/workflow.md` § Worktree paths, and one line in hunt: "Task temporaries (logs, evidence drafts, caches, venvs, test basetemps) go in `<worktree>/.tmp/`, never in bare `/tmp`."
- **Who creates it:**
  - hunt, or any first use, creates `.tmp/`.
  - hunt adds `.tmp/` to `$(git rev-parse --git-common-dir)/info/exclude` once per repo. No project `.gitignore` needs a commit, and the same exclude covers every worktree of that repo.
- **Owner:** the worktree, and therefore the task. This needs no runtime support, so Claude, Codex and Pi behave identically. An adapter may add convenience; for example, a Claude SessionStart could print the path. The rule never depends on that.

**Lifecycle points:**
- **Command or test completion:** unchanged source hygiene (`mktemp -d` plus a `trap`, `tmp_path`) stays the code author's job. For heavy test runs only, set `TMPDIR=<worktree>/.tmp` per command, never session-wide. Unix socket paths are capped at 108 bytes, and worktree paths are long; this is the same reason on-end.sh refuses to relocate the runtime root.
- **Task end (roar):** roar's preflight removes `.tmp/` along with `.panel/` and `build/panel-head/` (the 0948 purge list), after anything worth keeping is committed or posted to the PR. Required review evidence is by definition not in `.tmp/`; if a verdict needs it, it is committed. Then the worktree removal takes everything with it.
- **Crash recovery (molt):** `worktree-gc.sh` adds `.tmp/` to the same purge list. It already applies the rails (live cwd, live-pid lock, real WIP, self) before purging, so a crashed session's temporaries go when its branch is gone and nobody stands in the tree. A live session or a WIP tree keeps its `.tmp/`.
- **No worktree** (Imagine or explore on main): Claude uses its scratchpad, which is already managed. Other runtimes use `<primary>/.tmp/`, which is ignored the same way and swept by nothing. This is visible and the author can accept it; it is small in practice (inference).

**Deletes or replaces:**
- It replaces the ad-hoc `/tmp/tNNNN-*` habit, which is 95% of usage.
- It deletes no existing code. It adds one path to an existing list, and that list ideally becomes one shared constant used by both `worktree-gc.sh` and `close-and-clean.sh`; if they currently duplicate it, that is a small deletion.
- It also moves the bytes from RAM-backed tmpfs to disk, which by itself removes the "Disk full in every session at once" failure mode.

**To verify before implementing (inference):**
- `git worktree remove` does not count ignored files as dirty. I believe it does not, but a positive control must confirm it: make a worktree, write `.tmp/x` with an exclude, remove it, and expect success. Without that control, the purge-list step is still enough on its own.
- Whether `status --porcelain --untracked-files=all` in `worktree-gc.sh` hides an excluded `.tmp/`. It should, which makes the purge a formality.

**Verification plan:**
- Extend `tests/test_on_end_hook.py`'s sibling (the worktree-gc tests) and the roar preflight tests with three cases, all on throwaway repos under pytest `tmp_path`, run serially:
  1. A merged, clean tree with a populated `.tmp/` is removed.
  2. A live-cwd tree with `.tmp/` keeps it.
  3. A tree with real WIP plus `.tmp/` keeps both and reports the WIP.
- A grep test asserting that the skills write no literal `/tmp/` paths.
- Field check: re-run the `du` survey a week after landing.

**Price:** about 2–3 agent-hours (about $25–45), 0.5 author-hour (decision plus one review). There is a residual risk: agents keep using bare `/tmp` out of training habit. The rule costs nothing to restate, and Option C's report catches violations.

## Option B: a per-task registered temp root on the temp base

**Mechanism:**
- `scripts/task_tmp.sh <task-id>` returns `${TMPDIR:-/tmp}/idh-$UID/<repo-key>/<task-id>/` and writes an `owner` file inside it (repo, worktree path, branch, runtime, pid).
- roar removes its own task's root.
- molt sweeps a root when its worktree is unregistered or its branch is upstream-gone, and no live process holds it. The sweep reuses `session_scratch.py`'s liveness union, extended from session ids to task roots.
- It keeps temporaries on tmpfs, which is faster for caches.

**Deletes:** nothing. It adds about 150 lines and about 10 tests, and it creates a second liveness implementation, or a refactor of `session_scratch.py` into a shared module.

**Preservation:** the liveness rails and the ownership file. Remote and other-host sessions are invisible to liveness, which is the known 0338 limit, so it needs the same age rail as the session sweep.

**When it wins:** only if a measured need for tmpfs speed appears, or if most temporary work happens outside any worktree. Neither is demonstrated.

**Price:** about 8–12 agent-hours (about $100–180), 1.5 author-hours, plus permanent upkeep of a fourth lifecycle mechanism.

## Option C: do almost nothing (rule plus report)

**Mechanism:**
- The one-line rule from Option A ("never bare /tmp; scratchpad or worktree").
- Healthcheck check 12 is widened from the Claude root to a report-only top-N of the user's `/tmp` entries by size, with owner and mtime. It never deletes.
- The author or molt reads the report and deletes by hand.
- Reboots of the tmpfs host remain the crash recovery.

**Deletes:** nothing. It adds about 20 lines to the existing scan.

**Preservation:** trivially satisfied, because nothing is deleted automatically.

**Price:** about 1 agent-hour (about $10–15), 0.25 author-hour, plus recurring author-minutes at every cleanup. That recurring cost is exactly what the author complained about.

## Assessment

| | A: in-worktree `.tmp/` | B: registered task root | C: rule plus report |
|---|---|---|---|
| Addresses the demonstrated 95% | yes (moves it into an owned lifecycle) | yes | only by manual action |
| New mechanisms | 0 (extends the 0948 purge list) | 1, plus a liveness duplicate | 0 |
| Works on Codex/Pi with no adapter | yes | yes | yes |
| Live, WIP and evidence safety | inherits the worktree-gc rails | new rails to prove | n/a |
| Off tmpfs (RAM) | yes | no | no |
| Price | about $25–45 | about $100–180 | about $10–15 plus recurring |

**Recommendation:** Option A. Option C's report line can be added later, only if a violation of the rule recurs.

**What the harness does not own:** project tests that leak through `TMPDIR`, as in doudou's case. Those stay in project tickets; the harness only documents the per-command `TMPDIR=<worktree>/.tmp` idiom.

**Open question for the author:** should the 11G already sitting in `/tmp/t2093-*` and `/tmp/t2094-*` be checked for evidence and removed by hand now? That is a one-off, outside this design.
