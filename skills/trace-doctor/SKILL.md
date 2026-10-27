---
metadata:
  category: memory
name: trace-doctor
description: "Monthly survey of Claude Code session-trace economics: cost census, hypothesis statistics, ranked cost-saving report cross-referenced to tickets. Never auto-applies; files tickets for findings."
user-invocable: true
argument-hint: "[--days N]"
---

Analytical survey with ordinary judgment; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Trace Doctor $ARGUMENTS

Survey the session-trace corpus, interpret the numbers against the settled
phase 3–4 playbook, and emit a ranked cost-saving recommendation report. Run
monthly or on-demand. `$ARGUMENTS` accepts `--days N` (default 28).

**Authority boundary**: report and propose only. This skill runs the committed,
zero-LLM survey scripts, interprets their output, and opens tickets for
actionable findings. It never edits skills, rules, or scripts itself, and it
never commits per-session trace content — the numbers below are aggregates.

**Shadow dollars**: every `$` this skill reports is a list-price API-equivalent
under subscription auth — capacity consumption (rate limits, context budget),
never invoiced money. State this in the report header, as the phase-4
counterfactuals note does.

## 1. Survey

Run the six committed, standard-library-only scripts with the harness's
`python3` interpreter. They do not require a package-manager environment.
All intermediate outputs go to a scratch
directory; nothing here is tracked. `$ARGUMENTS` (e.g. `--days 14`) passes
straight through to each script's own `--days` argparse flag (default 28) —
there is no shell-side day parsing to keep in sync.

```bash
HARNESS_DIR="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"
cd "$HARNESS_DIR"                                         # cache paths below are repo-relative
SCRATCH=$(mktemp -d)

# Census, compaction advisory and friction scan are independent full-corpus walks (none
# consumes another's output) — run them concurrently.
python3 "$HARNESS_DIR/scripts/trace-stats.py" $ARGUMENTS \
  --output "$SCRATCH/census.csv" --json > "$SCRATCH/census-summary.json" &
python3 "$HARNESS_DIR/scripts/trace-compact-audit.py" $ARGUMENTS \
  --output "$SCRATCH/compact-audit-rows.csv" --json > "$SCRATCH/compact-audit.json" &
python3 "$HARNESS_DIR/scripts/trace-friction.py" $ARGUMENTS \
  --output "$SCRATCH/friction-daily.csv" --json > "$SCRATCH/friction.json" &
python3 "$HARNESS_DIR/scripts/trace-wall-time.py" $ARGUMENTS \
  --json > "$SCRATCH/wall-time.json" &
wait

# Forge join: reads AND writes the accumulating committed cache (do not create a
# new dated cache). Add --no-network if the forge is unreachable, and say so in
# the report.
python3 "$HARNESS_DIR/scripts/trace-pr-join.py" \
  --census "$SCRATCH/census.csv" --cache conception/trace-pr-join-2026-06.csv

# Hypotheses: the compact-audit --json → --compact-audit-json routing IS the
# adopt-item-#3 wiring — the compaction detector's output is consumed here as H8.
python3 "$HARNESS_DIR/scripts/trace-hypotheses.py" \
  --census "$SCRATCH/census.csv" \
  --compact-audit-json "$SCRATCH/compact-audit.json" \
  --pr-stats conception/trace-pr-join-2026-06.csv \
  --output "$SCRATCH/hypotheses.json"
```

Parse `$SCRATCH/hypotheses.json`, `$SCRATCH/census-summary.json` and `$SCRATCH/friction.json`. If the
census is empty (no agents in the window), report "no traces in window" and
stop.

If `trace-pr-join.py` changed `conception/trace-pr-join-2026-06.csv` (the join
resolved new PRs), that single cache file is the *only* tracked artifact this
run may commit; commit it on a branch landed through a merge request, with a named add:

```bash
git add conception/trace-pr-join-2026-06.csv    # the newly resolved rows only
git commit -m "chore(trace-doctor): accumulate forge-join cache"
```

## 2. Interpretation

Read the hypothesis statistics against the two settled playbook tables — do not
re-derive verdicts, apply them:

- **Ranking table** — `conception/trace-hypotheses-2026-06.md` § Ranked
  recommendations: which lever holds the most `$/week at stake` and whether the
  bound is upper or lower.
- **Routing table** — `conception/trace-counterfactuals-2026-06.md` § Routing: the
  settled disposition of each recommendation (adopt now / phase-5 A/B / reject),
  the refined `$/week`, and why. The disjoint-bucket dedup total there
  ($2,356 = 34.8%) is the addressable ceiling — do not sum overlapping buckets
  on top of it.

For the current window, compare each hypothesis statistic against its settled
number and flag material drift (a bucket that grew or shrank by more than, say,
a third), which is what a monthly re-measure is for. The compaction advisory
(H8, from the wired compact-audit input) is reported as an advisory count of
missed compact/clear runs, not an A/B.

Report `inherited_turns_dropped` from the compact-audit summary alongside H8.
It counts turns a forked or resumed session replayed from its parent, which the
audit attributes to the parent only. A non-zero count is normal; a *large* one
means the window is fork-heavy, so H8's run count reflects fewer distinct
sessions than `agents_in_window` suggests. An H8 figure from an older census
may be inflated by the same effect.

### Velocity (friction) section

Cost does not rank turns and wall-clock, so report velocity separately, from
`friction.json`, ranked in **hours**, not dollars (method and caveats:
`conception/2026-10-21-velocity-friction-scan.md`):

1. **Tool wall-clock over 30 s, by tool** (`slow_by_tool_hours_upper_bound`),
   largest first. Every duration is tool_use to tool_result, so it includes
   permission waits and background commands: label each figure "upper bound".
   `AskUserQuestion` hours are the author's own latency, not tool friction;
   list them apart. When the Bash tail is mostly test or gate commands, the
   remedy is a consultation, not a ticket: run lair's step 13 gate survey
   for each project concerned and offer `/test-doctor` with what it prints,
   passing an inconclusive line on as lair does. Only the author starts the
   consultation.
2. **Wait commands** (`wait_commands`, `wait_hours_upper_bound`). The regex runs
   on the command minus quoted strings and heredoc bodies; durations are
   still an upper bound: say so.
3. **Tool errors by cause** (`errors_by_cause`: worktree guard, no such tool,
   write outside worktree, other) with `error_hours_upper_bound`.

Always show the **daily series** (`daily`, or `friction-daily.csv`) beside any
period total, and state the current rate (last 3 days) of each cause next to
its window total. A class that stopped (zero for days) is history, not a
lever; a class that is rising is the finding. Price only what the series
shows still happening. "Other" errors are a residual: do not name a cause for
it without reading samples. Findings enter step 3 like any lever; this
section never applies a fix.

### Follies section

From the same `friction.json`, report the `follies` block: a repeated mistake
is a defect of the harness, not of one session. One row per folly
(`pgrep_self_match`, `sleep_poll_to_cap`, `repeat_failing`): count, sessions,
`seconds_upper_bound` and `seconds_lower_bound`, runtime split, and the `rung`
of the barrier ladder it maps to (table `folly_barrier`: fix the primitive, a
per-command cap, a PreToolUse hook, an instruction last). `--folly-min-seconds N`
counts only calls of at least N seconds, for every folly. Every figure is a
bound: traces record no job end, so never write "hours given back" and never
turn the bounds into a point estimate. The rung is a table, not a verdict; no
prescription is applied here.

Report `barrier_denials` as data: how often each worktree guard refused a call
(`unattributed` = blocked, guard not identified). Do not propose keeping or
deleting a barrier: that verdict belongs to test-doctor (`rules/workflow.md`, "No
guards on guards"). For the arena's Pi sessions, run
`python3 "$HARNESS_DIR/scripts/trace-friction.py" --pi-runs <runs dir> --json`;
it never prints a command text.

### Where time goes: raid, hunt, gaze

From `wall-time.json` (method and limits: the docstring of
`$HARNESS_DIR/scripts/trace-wall-time.py`), one block per skill, in hours:

1. **Runs and wall**: run count, `nested_in_raid` for hunt, median and p90
   wall. A hunt inside a raid appears in both views; never add them.
2. **Orchestrator split** (the run's own trace, its critical path):
   generation, test/gate, poll/wait, background-wait (blocked on spawned
   agents or background commands), forked-skill (waiting on a forked skill
   such as gaze or verify-adherence), human and human-away (gaps over 30 min:
   the author absent, not a reply), idle-tail. Report human-away apart: it
   is the author's latency, not harness time.
3. **Tree split** (agent-seconds summed over the run and its descendants):
   where parallel work goes. Generation is model latency, a route lever;
   poll/wait and background-wait are wait-primitive levers; test/gate is a
   gate-survey lever (offer `/test-doctor` as in the velocity section).
4. **Redundant testing**: test runs, and reruns of the same gate class in the
   same worktree with no mutation in between, after a pass and after a
   failure, with their minutes. A heuristic estimate; a test of the same
   commit in another worktree (a review seat) is not counted.
5. **Blockers**: the longest summed waits by command or tool. A hand-rolled
   idle or poll loop near the top is a follies candidate.

Every gap is READ; every category is a heuristic. A finding enters step 3 like
any lever; this section never applies a fix.

### Treatment follow-up section

After the velocity section, report whether each past fix moved its error
class. Closed tickets declare `Treats:` and `Baseline:` body lines
(convention: `conception/trace-treatments.md`); the script dates each merge from git
history and compares the class's daily rate before and after, from the same
`friction.json`:

```bash
python3 "$HARNESS_DIR/scripts/trace-treatments.py" \
  --friction-json "$SCRATCH/friction.json"
```

Show one row per treatment: ticket, class, merge date, rate and day count
before and after, and the verdict (`improved`, `unchanged`, `worse`,
`too_few_days` under 7 days after the merge, `unmeasured`). Report
`unmeasured` as unmeasured, never as improved. A `worse` or `unchanged`
verdict enters step 3 as a lever proposal; this section never closes or
reopens a ticket. Treatments need a window reaching the merge date: widen
`--days` if the merge is older than the survey.

## 3. Cross-reference existing tickets

For each actionable finding, decide whether it is already owned. Search open
and recently-closed tickets for the lever's keyword:

```bash
ERG=$(command -v erg 2>/dev/null || echo "tickets/erg")
$ERG ready --json tickets/ 2>/dev/null || true
grep -rl "trace-doctor\|micro-turn\|verification convergence\|model right-sizing" tickets/ 2>/dev/null | tail -10
grep -rl "<lever-keyword>" tickets/closed/ 2>/dev/null | tail -5
```

Mark each finding `covered` (an open ticket owns it), `recently-fixed` (a
closed ticket within ~14 days), or `uncovered`.

## 4. Report

Present the ranked recommendations as a table, shadow-dollar disclaimer in the
header:

| Rank | Lever | $/wk (refined) | Bound | Routing | Ticket status |
|------|-------|----------------|-------|---------|---------------|

For each `uncovered`, actionable finding, show:
- **Evidence**: the aggregate statistic from `hypotheses.json` (no per-session data)
- **Settled routing**: the disposition from the counterfactuals routing table
- **Proposed action**: the concrete next step (a prompt-rule, an A/B, an advisory)

The report lands in the invocation's output (or a `conception/` note if the caller
asks); it is never written as tracked per-session data.

## 5. Open tickets for uncovered findings

For each `uncovered` finding the author approves, create a ticket:

```bash
$ERG new "trace-doctor: <lever> — <one-line action>"
```

- **Context**: the aggregate statistic, its settled routing, the `$/wk` at stake
- **Actions**: the concrete step (prompt-rule diff, A/B design, advisory wiring)
- **Test**: how to confirm the lever moved next census
- **Exit criteria**: the condition that retires the finding

Commit the new tickets on a branch landed through a merge request, naming each
file (never a blanket add in the shared `tickets/` checkout):

```bash
git add tickets/<id>-<slug>.erg          # name each new ticket file, one per add
git commit -m "chore(trace-doctor): open N tickets from monthly survey"
```

## 6. Done

Report:

```
trace-doctor: surveyed {days}d window — {agents} agents, ${total} shadow, {slow_h}h tool tail (upper bound), {uncovered} uncovered levers, {ticketed} tickets opened
```
