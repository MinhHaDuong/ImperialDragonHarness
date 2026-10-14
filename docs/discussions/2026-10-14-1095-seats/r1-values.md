# R1, author's values seat (SIMULATED): excellence, integrity, kindness

Every position below is SIMULATED. The real author decides. I checked the
architect's claims against `scripts/worktree-gc.sh`,
`scripts/worktree-exit-preflight.sh`, `skills/molt/SKILL.md` and ticket 1095.
I deleted nothing and ran no tests.

## Grounding facts that change the assessment

1. **An excluded `.tmp/` is invisible to the WIP rail.** Both the gc script and
   the exit preflight decide "clean" with `git status --porcelain
   --untracked-files=all` (gc line 154 onward, preflight line 52). A path listed
   in `info/exclude` never appears in that output. Under Option A, whatever sits
   in `.tmp/` is therefore deleted with no blocker and no report. The
   architect's "inherits the worktree-gc rails" holds for the liveness and lock
   rails. It does not hold for the WIP rail. For `.tmp/` that rail reports
   all-clear without being able to look.
2. **`worktree-gc.sh` works on one repo**, `${1:-.}`. Crash recovery for a
   project worktree, such as the t2093/t2094 case, happens only when molt runs
   in that project. The architect's table does not say this.
3. **gc only acts once a branch is gone.** If a session crashes on an unmerged
   branch, its `.tmp/` stays until someone resolves the branch. That is safe,
   but unbounded. Off tmpfs, the bytes then fill the home disk, which is backed
   up by restic, instead of RAM.
4. **The ticket defines the request as WHERE and HOW in the work cycle,
   covering three points**: command or test completion, roar, and
   startup/molt recovery.

## Option A: worktree `.tmp/` (SIMULATED assessment)

- **Excellence: high.** It answers the real request: one owner and one place,
  with lifecycle points the harness already has. It deletes the category of
  leak instead of adding a sweeper. It also helps at 3 a.m.: tmpfs exhaustion
  hits every session at once, and a full home disk is slower and louder.
- **Integrity: one real hole, with two parts.**
  - "Required review evidence is by definition not in `.tmp/`" solves the
    problem by definition, not by mechanism. An agent that parks a gaze log,
    benchmark output or audit JSON in `.tmp/`, as the t2093/t2094 evidence dirs
    were parked, loses it silently at gc, because of fact 1.
  - The contract has to make `.tmp/` *declared disposable*. Roar needs an
    explicit "promote, then purge" step, and the purge has to report what it
    removed (path count and size) rather than run silently.
  - The two items the architect flagged for verification (does `worktree
    remove` treat ignored files as dirty, and does status hide `.tmp/`) are the
    right positive controls. They must run before anyone claims the purge is a
    formality.
- **Kindness: good, with friction at the edges.**
  - Long paths break Unix sockets: the 108-byte cap. That is why `TMPDIR` is
    set per command only; the rule should say so in one line, so that agents
    do not discover it as an opaque failure.
  - Codex and Pi sessions with no worktree fall back to `<primary>/.tmp/`,
    which nothing sweeps. It is visible but has no owner. Here the residual is
    named and left open, which I accept only if a report surfaces it.
  - Editing `info/exclude` in project repos is a quiet mutation of someone
    else's repo config. It is harmless, but hunt should print that it did it.
- **Highest-value change:** make cleanup *visible*, so the rule's only failure
  mode (training-habit `/tmp` use) can be seen. Concretely: before purging,
  roar and gc each print `removed .tmp/ (N files, X MB)`, and Option C's
  report-only top-N of bare `/tmp` comes with A from day one, not "later if a
  violation recurs". Without the report, the residual risk the architect named
  cannot be observed. Saying "the rule works" would then be a null result with
  no positive control.

## Option B: registered task root (SIMULATED assessment)

- **Excellence: medium.** It keeps tmpfs speed, but nobody has measured a need
  for it, and it builds a fourth lifecycle mechanism. The 0854 history argues
  against a second liveness implementation: two implementations drift apart.
- **Integrity: the most honest about ownership.** The `owner` file says who
  made what. It is the least honest about safety, though:
  - It inherits the 0338 remote-session blind spot.
  - It needs an age rail. That rail is scoped to owned roots, so it is not
    "generic age-based rm of /tmp", but in practice it brings age-based
    deletion back.
  - Its new rails have to be proven from scratch, with roughly 10 new tests
    that are each a chance for a check that cannot see.
- **Kindness: poor.** It costs the most author-hours and adds permanent
  upkeep, and the bytes stay in RAM, which is where "Disk full everywhere"
  starts. One gain is real: it serves no-worktree sessions on every runtime
  equally.
- **Highest-value change:** cut it down to the one thing it does better than
  A. Do not build a liveness sweep. Use `task_tmp.sh` only as A's fallback for
  sessions that have no worktree, with no automatic deletion and only a report.

## Option C: rule plus report (SIMULATED assessment)

- **Excellence: low as a design.** It answers a narrower proxy: it tells us
  where the bytes are, not where cleanup sits in the cycle. The author's
  complaint was the recurring manual cleanup, and C keeps exactly that.
- **Integrity: strong.** It deletes nothing and claims nothing. One condition:
  the report must say "could not read N entries" rather than show a short list
  that looks clean. As written, entries owned by other users or unreadable
  ones would just drop out.
- **Kindness: cheap now, but every cleanup costs author attention, which the
  author values most.**
- **Highest-value change:** let it act on the one class it can prove it owns.
  Entries named after a ticket of a *closed* ticket in a known repo are
  proposed for deletion in one batched yes/no question, listed with sizes,
  instead of being left to hand work.

## Cross-cutting (SIMULATED)

- **The 11G already sitting in t2093/t2094 is not housekeeping. It is
  evidence of unknown status.** It belongs to another project. That project's
  session should check whether a verdict cites it, and then archive or delete
  it. It is not this harness's sweep to make.
- **Doudou's pytest quota is a project leak,** and it is fixed there. The
  harness should only document the per-command `TMPDIR` idiom. I agree with the
  architect.

## Ranking (SIMULATED)

1. **A, with the visibility change** (purge reports what it removed; C's
   report ships with it). This is the best work, needs no new mechanism, and
   moves the bytes off RAM. The hole is fixable for about +1 agent-hour.
2. **C.** It is honest and harmless, but it leaves the author doing the
   recurring work they asked to stop doing.
3. **B.** It costs more than its benefits justify, reintroduces age-based
   deletion, and duplicates liveness logic. Its only unique merit, covering
   no-worktree runtimes, is better taken as a report-only fallback inside A.

| Option | The one change that most raises it |
|---|---|
| A | Declare `.tmp/` disposable with a roar "promote, then purge" step; every purge prints what it removed; ship the bare-`/tmp` report together with A |
| B | Shrink it to a no-worktree fallback path with an owner file and report-only handling, no sweep |
| C | Count entries it could not read, and turn closed-ticket entries into one batched delete proposal |
