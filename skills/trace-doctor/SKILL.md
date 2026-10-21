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

Run the five committed, standard-library-only scripts with the harness's
`python3` interpreter. They do not require a package-manager environment.
All intermediate outputs go to a scratch
directory; nothing here is tracked. `$ARGUMENTS` (e.g. `--days 14`) passes
straight through to each script's own `--days` argparse flag (default 28) —
there is no shell-side day parsing to keep in sync.

```bash
HARNESS_DIR="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"
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
wait

# Forge join: reads AND writes the accumulating committed cache (do not create a
# new dated cache). Add --no-network if the forge is unreachable, and say so in
# the report.
python3 "$HARNESS_DIR/scripts/trace-pr-join.py" \
  --census "$SCRATCH/census.csv" --cache docs/trace-pr-join-2026-06.csv

# Hypotheses: the compact-audit --json → --compact-audit-json routing IS the
# adopt-item-#3 wiring — the compaction detector's output is consumed here as H8.
python3 "$HARNESS_DIR/scripts/trace-hypotheses.py" \
  --census "$SCRATCH/census.csv" \
  --compact-audit-json "$SCRATCH/compact-audit.json" \
  --pr-stats docs/trace-pr-join-2026-06.csv \
  --output "$SCRATCH/hypotheses.json"
```

Parse `$SCRATCH/hypotheses.json`, `$SCRATCH/census-summary.json` and `$SCRATCH/friction.json`. If the
census is empty (no agents in the window), report "no traces in window" and
stop.

If `trace-pr-join.py` changed `docs/trace-pr-join-2026-06.csv` (the join
resolved new PRs), that single cache file is the *only* tracked artifact this
run may commit; commit it with a named add:

```bash
git add docs/trace-pr-join-2026-06.csv    # the newly resolved rows only
git commit -m "chore(trace-doctor): accumulate forge-join cache"
```

## 2. Interpretation

Read the hypothesis statistics against the two settled playbook tables — do not
re-derive verdicts, apply them:

- **Ranking table** — `docs/trace-hypotheses-2026-06.md` § Ranked
  recommendations: which lever holds the most `$/week at stake` and whether the
  bound is upper or lower.
- **Routing table** — `docs/trace-counterfactuals-2026-06.md` § Routing: the
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
`docs/2026-10-21-velocity-friction-scan.md`):

1. **Tool wall-clock over 30 s, by tool** (`slow_by_tool_hours_upper_bound`),
   largest first. Every duration is tool_use to tool_result, so it includes
   permission waits and background commands: label each figure "upper bound".
   `AskUserQuestion` hours are the author's own latency, not tool friction;
   list them apart.
2. **Wait commands** (`wait_commands`, `wait_hours_upper_bound`). The regex is
   tightened but still counts keywords quoted in heredocs: say "upper bound".
3. **Tool errors by cause** (`errors_by_cause`: worktree guard, no such tool,
   write outside worktree, other) with `error_hours_upper_bound`.

Always show the **daily series** (`daily`, or `friction-daily.csv`) beside any
period total, and state the current rate (last 3 days) of each cause next to
its window total. A class that stopped (zero for days) is history, not a
lever; a class that is rising is the finding. Price only what the series
shows still happening. "Other" errors are a residual: do not name a cause for
it without reading samples. Findings enter step 3 like any lever; this
section never applies a fix.

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

The report lands in the invocation's output (or a `docs/` note if the caller
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

Commit the new tickets naming each file (never a blanket add in the shared
`tickets/` checkout):

```bash
git add tickets/<id>-<slug>.erg          # name each new ticket file, one per add
git commit -m "chore(trace-doctor): open N tickets from monthly survey"
```

## 6. Done

Report:

```
trace-doctor: surveyed {days}d window — {agents} agents, ${total} shadow, {slow_h}h tool tail (upper bound), {uncovered} uncovered levers, {ticketed} tickets opened
```
