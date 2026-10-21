# Stopguard: end-of-turn hook, design and implementation plan

Status: proposal, revised after the Fable, Astra and KISS reviews (§8). The log
location is decided (§4). Nothing is implemented, and the ticket tracker is
deferred: the plan below describes work to do once the author lifts the
deferral. Written 2026-10-21 in session "Stopguard".

## 1. Problem and goal

An agent that ends its turn at the wrong moment breaks the assembly chain and
costs the author a manual wakeup. Two stop patterns are in scope:

1. **Ask without asking up.** The turn ends on a question to the author and no
   higher model was consulted first (`rules/workflow.md` § Escalation
   protocol, "Ask up first").
2. **Wait with no wake-up.** The turn ends because the agent waits on an
   external process (automerge, CI, a launched reviewer) and nothing tracked
   will notify it.

Goal: observe both patterns in live sessions, measure how often a stop is bad,
and only then let the hook refuse a stop. The first release observes and logs;
it never refuses.

Non-goals: judging the content of a question, subagent stops, headless
workers, replacing `/perch` or `/lair`.

## 2. Evidence the mechanism exists

Smoke-tested 2026-10-21 in headless mode, with a local settings file or inline
config, not the production install path. One throwaway hook per harness blocked
the first stop with a reason and let the second one through; all three agents
resumed and answered the injected instruction.

| | Claude Code 2.1.306 | Codex (`codex exec`) | Pi 1.3.0 (`-p`) |
|---|---|---|---|
| Event | `Stop` | `Stop` | `agent_before_settle` (after `turn_end`, `agent_end`) |
| Block | stdout JSON `{"decision":"block","reason"}` or exit 2 | same | extension: `pi.sendUserMessage(text, {deliverAs:"followUp"})` |
| Loop guard | `stop_hook_active`; cap of 8 consecutive blocks | `stop_hook_active` | none; the extension keeps its own flag |
| Payload used | `last_assistant_message`, `transcript_path`, `cwd`, `permission_mode`, `background_tasks` | `last_assistant_message`, `transcript_path`, `turn_id`, `cwd`, `permission_mode` | event object; `agent_end.messages` holds the text |

Probes and logs: `.smoke/` in the exploration worktree (untracked).

Gaps, closed first in phase 1 (each marked pass or fail in the PR):

- The Claude Code smoke bypassed the plugin `hooks.json` and `idh-hook`; rerun
  through the installed path with an explicit `"timeout": 5`.
- Codex: a project-local `.codex/hooks.json` did not load headless; an inline
  `-c hooks.Stop=[...]` did. The global `~/.codex/hooks.json` install
  (`bin/idh install`) is untested, and a new `Stop` entry changes the trusted
  definition, so each host re-trusts it through `/hooks`.
- Codex `last_assistant_message` may be null; Pi's last text must come from
  `agent_end.messages` (shape unverified).
- Interactive sessions on all three, and the `permission_mode` values each
  reports.

## 3. Architecture

One canonical Python program, standard library only, three thin adapters.

```
scripts/stop_guard/
  run.py        entry: read stdin, build Turn, run rules, log, emit
  turn.py       Turn record + per-harness normalizers (claude, codex, pi)
  registry.py   explicit list of rule modules, one import per line
  rules/ask_up.py, rules/pending_wait.py
  config.json   {"ask_up": "dry", "pending_wait": "dry"}   dry | enforce
tests/stop_guard/   fixtures per rule, runner tests, one smoke per harness
```

**Turn**, the only thing a rule sees:

```
harness, session_id, turn_index, cwd, host, ts, permission_mode, interactive,
text (bounded last message), flags (ends_in_question, asked_up_marker,
wait_vocab_hit, truncated), stop_hook_active, background_tasks (list|None)
```

The runner computes `flags` from the whole bounded message before keeping a
tail, so a code fence opened or a marker written early in a long message is
still seen. A message over 256 KB is skipped and logged `oversize`.

**Rule contract:** `check(turn) -> Finding | None`, a pure function: no I/O, no
clock, no environment. Adding or removing a rule is one file in `rules/`, one
line in `registry.py`, one key in `config.json`. The registry is an explicit
list, not directory discovery.

**Rule 1, ask-up.** Trigger: the final non-empty line outside a code fence ends
with `?`. In v1 the log records only whether `Asked up:` appears in the message
(`asked_up_marker`); the full marker vocabulary arrives with enforcement (§6,
phase 5).

**Rule 2, pending wait.** Trigger: a wait vocabulary hit (automerge,
"waiting for", CI, reviewer launched, "will be notified"). The log records the
hit, and on Claude Code the `background_tasks` ids. Nothing in v1 establishes
that a wait will wake the agent, so the rule only counts and never judges; the
pass condition arrives with the waiter (§6, relation).

**Modes**, per rule: `dry` and `enforce`. In v1 every rule is `dry`: the finding
is logged and the stop is never refused. Removing the registry line disables a
rule.

**Emission.** In `dry`, stdout is empty (Codex rejects plain-text stdout on
`Stop`); the log is the only output.

**Execution contract.** Runner deadline 2 s; adapter timeout 5 s; stdin capped
at 256 KB. On any error, timeout, killed child or malformed output the stop is
allowed. The adapter, not the runner, logs a failure line when the child exits
non-zero or times out, because a killed runner cannot log its own failure.

**Adapters:**

- Claude Code: `Stop` entry in `adapters/claude-code/hooks/hooks.json`, through
  `idh-hook`, `"timeout": 5`.
- Codex: `Stop` entry in `adapters/codex/hooks.json`, same launcher.
- Pi: `adapters/pi/extensions/stop-guard.ts` on `agent_before_settle`; in `dry`
  it spawns `run.py` and logs.

### Enforce stage (built in phase 5, not before)

Enforcement is deferred behind measurement; this is what it needs, recorded so
the v1 log fields support it.

- **Where it may run.** Only in interactive sessions: `permission_mode` in
  `default`, `plan`, `acceptEdits` (Claude Code, Codex) or `ctx.mode == "tui"`
  (Pi). Headless workers (`-p`, `codex exec`, `/raid` and `coder` children, Pi
  `--no-session` children) cannot ask up and stay `dry` permanently. An unknown
  or missing discriminator means `dry`.
- **Block.** `{"decision":"block","reason":"<one declarative sentence>"}` per
  `rules/claude-code.md` § Hook output. Never block when `stop_hook_active` is
  true; at most one block per stop. Pi maps a block to a `followUp` message with
  a flag per turn (reset on `turn_start` and on user input, keyed by
  `turnIndex`).
- **Markers**, written by agents in the final message, with the producer line
  added to `rules/workflow.md` § Escalation protocol in this phase:
  `Asked up: <model> said <answer>` (consulted),
  `ask-up: author's call (scope|money|irreversible)` (justified),
  `ask-up: unreachable <model>` (unavailable); any other text after `ask-up:` is
  a bypass. Compliance is reported as consulted, justified or unavailable, and
  bypass; a marker alone is never counted as a successful recovery.

## 4. Log: local spool, durable results in the repo

Writing a tracked log live from the hook fails two rules: `rules/git.md`
(main is read-only; a hook appending to a tracked file dirties `main` and
breaks `scripts/sync-local-main.sh`) and AGENTS.md § Project memory boundary
(a hook runs in every project's sessions and would carry their content into the
harness repo, which is public). Replay does not need a committed raw log: session
files measured 2026-10-21 hold Claude Code 5,552 files back to 2026-06-10
(`cleanupPeriodDays` 180), Codex 2,085 back to 2026-09-08, Pi 60 back to
2026-09-16.

**Decision (author, 2026-10-21): local spool, durable results in the repo.**

1. **Spool, untracked, per host.** One line per stop appended to
   `~/.local/share/idh/stopguard/<host>/<yyyy-mm-dd>.jsonl`: `schema_version`,
   `rule_versions`, event id (`session_id:turn_index:hash(tail)`), harness,
   session id, transcript path, turn index, `permission_mode`, flags, findings,
   `background_tasks` ids, message length, latency, errors (truncated to 500
   characters so a line stays under 4 KB). No message text. Every stop is
   logged, findings or not: a line with `findings: []` is the heartbeat, so "the
   hook did not run" differs from "nothing found". Files older than 180 days
   are pruned by the report step. Spools on a shared filesystem are unsupported.
2. **Weekly report, tracked.** `report.py` writes
   `docs/stopguard/reports/<yyyy>-W<ww>-<host>.md` from the local spool, one
   small PR from `/lair` or `/molt`. `.gitignore` is a deny-list with explicit
   allows and `docs/**` is allowed; a root `telemetry/` directory would be
   silently ignored, so reports and labels live under `docs/stopguard/`. A test
   asserts the first report file is git-visible.
3. **Labeled set, tracked.** `docs/stopguard/labels/<rule>/<yyyy-mm-dd>.jsonl`:
   event id, harness, flags, label, one-line rationale. No message text; the
   transcript path gives the text while the session file exists.

Spool size, assumed and unmeasured: about 500 bytes per line, 200 stops per
day per host, so about 36 MB per year on local disk.

## 5. Review

### 5.1 Portability

Payloads differ, so rules never see one; `turn.py` is the only per-harness code
besides the three adapters. `background_tasks` is `None` on Codex and Pi. Pi's
adapter is TypeScript where the others are registrations: the same size of job,
shipped together. Codex needs the global install. Linux only.

### 5.2 Concurrency

- **Within a machine:** sessions append to one daily spool file; each write is
  one line under 4 KB, one `os.write` on a file opened `O_APPEND`, which does
  not interleave on a local Linux filesystem. No locks. The config changes by
  hand and rarely; a parse failure falls back to all-`dry` and logs.
- **Across machines:** spools are local and never shared. Reports are named
  with the host (unique per machine), label files by date and rule, so two
  machines never write the same tracked file. No cross-host aggregation.
- **Report jobs** are idempotent: same spool in, same bytes out, written to a
  temporary file and renamed. A report covers whole days and skips a trailing
  partial line.

### 5.3 Awkward sessions

| Scenario | Behavior |
|---|---|
| Hook crashes, times out, bad JSON | stop allowed; the adapter logs the failure |
| Empty or null last message (tool-only end, Codex null) | logged `no_text`, counted apart from a clean pass |
| Very long message | flags from the whole bounded message; over 256 KB skipped as `oversize` |
| `stop_hook_active` true | never block, log |
| User interrupt, API error | Claude Code fires no `Stop`; excluded from the eligible-stop denominator |
| Resume, fork | Claude Code `--resume` keeps the session id and transcript; only `--fork-session` mints a new id. The log keys on session id, transcript path and turn index; replay dedupes inherited records |
| Headless, `--no-session` children, subagents | not enforced; subagent stops are not registered |
| Spool unwritable, disk full | stop allowed, error to stderr, no retry |

### 5.4 Observability

One heartbeat line per stop. `report.py`, per rule per week: eligible stops,
invocation coverage, usable-text coverage, skipped checks (oversize, timeout),
errors, trigger rate, latency p50 and p99. Adapter-observed failures are logged
by the adapter, so a dead runner shows as a failure, not as silence. The three
headless smokes from §2 run as regression tests against a live install after
any adapter change.

### 5.5 Friction added

In `dry`: none visible to the model or the author; one process start per stop,
measured (M1). In `enforce`: every block, true positives included, costs one
continuation (a context re-read plus the marker turn), and a false positive is a
wasted turn. The gate in §7 keeps a rule in `dry` until measured precision
clears the threshold.

### 5.6 Expected costs and benefits

Agent cost and author benefit are different units and are not converted into
each other. The decision uses author-hours on both sides; agent spend is a
budget cap.

- **Agent side:** about 9.5 agent-hours (§6), spend capped at 30 USD for the
  build. The arena figure of 0.80 USD for one `claude-opus-5-5` task (a
  6-minute task, grid 2026-10-19) is a scale reference, not a unit price.
- **Author side:** about 3 author-hours one-off (§6) plus about 0.1 hour per
  week reading the report. Getting to the first decision (G1) costs 0.8
  author-hours.
- **Benefit:** `w` author-minutes saved per avoided bad stop, `n` bad stops
  avoided per week. Assumed `w = 3`, `n = 20` (a 1.4% bad-stop rate at 200 stops
  a day): 54 minutes net per week, payback `180 / 54`, about 3.3 weeks. All
  inputs are guesses; the labeling measures `n` (M4) and `w` (M7).
- **Gate G1, after the first replay:** if measured bad stops for Claude Code
  are below about 5 per week (9 net minutes, payback over 20 weeks), stop: keep
  the hook as telemetry and do not fund phases 3b, 4 and 5.

## 6. Implementation plan

Tickets per `rules/workflow.md`: a tracker with one child per phase, each PR
closing its own child, children `Blocked-by` their real prerequisite.

| Phase | Content | Exit | Agent h | Author h |
|---|---|---|---|---|
| 1 | Close the §2 gaps; `run.py`, `turn.py`, registry, both rules, `dry` only, spool writer, three adapters, fixtures, the three smokes as tests | each §2 gap pass or fail; green tests; a heartbeat on each harness from the live install; latency measured | 3.5 | 0.3 |
| 2 | `report.py`, coverage figures, git-visible report path, weekly report step in `/lair` or `/molt`, spool pruning | first report PR merged | 0.5 | 0.25 |
| 3 | Replay harness, Claude Code only: rebuild `Turn`s from session files, run the same rules, same log schema; each finding printed beside the author's next message and the time gap | measured bad stops per week (G1) | 2 | 0.25 |
| 3b | Replay for Codex and Pi (their histories are about 6 and 5 weeks); after G1 | per-harness trigger rates | 1.5 | 0.1 |
| 4 | Agent prepares about 60 findings per rule; author hand-labels the first 30 per rule, rules are frozen, the next 30 are the held-out set | precision with interval (M4) | 0.5 | 1.5 |
| 5 | Enforce stage (§3), `rules/workflow.md` marker line, Pi `followUp`, friction review after two weeks; rule 1 only unless the waiter exists | rule enforced or retired, with numbers | 1.5 | 0.5 |
| Total | | | about 9.5 | about 3 |

Dependencies: 1 → {2, 3}; G1 after 3; then 3b, 4 → 5. Phase 1 ships before
phase 3 so live data accumulates while replay is built.

### Relation to the await-external design

Another session designs the waiter that would give rule 2 a pass condition
(`docs/discussions/2026-10-21-await-external-design.md`, branch
`explore-await-external-*`, uncommitted): a detached systemd unit probes a
condition under a deadline and records one outcome, delivered by live push,
resume, or pull at session start. Agreed split: this component is the only
Stop-hook implementation, and the waiter's own Stop safety net is dropped from
its sequence. The waiter owns the registry
`${XDG_STATE_HOME:-~/.local/state}/idh/waits/<runtime>/<session>/`
(`wait.json`, `outcome.json`); once it exists, the runner reads it into a
`live_waits` field of `Turn` and rule 2 gains the pass kind "a wait is
registered with a delivery channel". Until then rule 2 only counts. Stopguard
depends only on the file layout; the waiter keeps field names stable or
announces a change. Paths: spool `~/.local/share/idh/stopguard/`, registry
`~/.local/state/idh/waits/`. Not verified on the waiter side: its probe list,
resume against a live TUI, whether a runtime kills the waiter at session end,
systemd `RuntimeMaxSec` behavior on this host.

## 7. Measurements

The labeler sees each finding beside the author's next message and the time gap;
there is no automatic classification in v1. Label definition: **avoidable
interruption**, meaning the author would have preferred the agent to continue,
or to ask a higher model first. Marker compliance is reported separately and is
not the label.

| # | Measure | Source | Gate |
|---|---|---|---|
| M1 | Hook latency p50 and p99, adapter spawn included | `hyperfine` over 1000 runs plus logged latency | p99 under 100 ms |
| M2 | Eligible stops per harness per week: turns ending in an assistant message, interrupts and API errors excluded | session files | denominator for M3, M4, M6 |
| M3 | Trigger rate per rule: triggers / eligible stops | replay and live log | reported |
| M4 | Precision per rule: labeled avoidable interruptions / triggers; rules frozen, 30 held-out findings per rule from Claude Code, Wilson 95% interval | hand labels | point estimate 0.8 or more and lower bound 0.6 or more to enforce; Codex and Pi reported as counts until their volume allows an interval |
| M6 | Coverage per harness: invocation coverage (hook runs / eligible stops), usable-text coverage, skipped checks, adapter-observed failures | log vs session files | invocation at least 99% of eligible stops; error rate under 0.5% |
| M7 | Author intervention time: gap from a bad stop to the author's next message | recorded at labeling | replaces the assumed `w` |

After phase 5, normalized per eligible stop: block rate, marker kinds, tokens
per block, block-then-pushback rate, and manual wakeups per week before and
after, as a before and after table.

Positive control before trusting any null: for each harness, a synthetic
payload that must trigger each rule runs through the live install and the log
must show it. A rule with zero live findings is reported as unproven until that
control has fired.

Limits of replay: past sessions have no markers, so replay measures the trigger,
not compliance; they have no `background_tasks` or waiter registry; and the
held-out split is by time, so a change in the author's phrasing between halves
shows up as a precision drop, which is the point.

## 8. Review record

- **Fable** (Anthropic, same family as the producer, so not independent):
  APPROVE WITH FIXES, 12 findings, 1 blocking (tracked paths ignored by
  `.gitignore`, verified and fixed in §4).
- **Astra** (`gpt-6-astra`, OpenAI, high effort, independent): REWORK, 11
  findings, 2 blocking (rule 2 pass condition does not prove a wake-up;
  measurements did not support the claimed benefit). Accepted as design
  findings; the REWORK verdict also cites the reviewer not rerunning the smoke
  tests.
- **KISS pass** (Sonnet, same family): moved enforcement, markers and the
  enforce-time mode resolution out of the first release, shrank rule 2 to a
  counter, merged phase 0 into phase 1, limited replay to Claude Code first,
  cut four of the measures, and fixed the held-out arithmetic.
- Spend was not recorded. The full finding-by-finding disposition is in the
  session transcript, not repeated here.
