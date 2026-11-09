# Waiting on external processes: design draft

Status: final draft v5, parked. Imagine phase. No ticket, no code. Revised
after an Opus review that corrected the first draft (outcome recording, resume
gate, sequence); v3 adds systemd as the waiter backend and three items from a
survey of other harnesses.

## Problem

An agent session that launched an external process (GitHub automerge, CI, a
reviewer in a headless TUI) must learn the result without polling that burns
tokens and without a wait loop that can run forever. The mechanism must work
on Claude Code, Codex and Pi. A single-runtime solution is not an answer.

Constraints, from existing rules:

- No foreground `--watch` or sleep loops (memory: no-blocking-waits; the
  incident was a `--watch` hung ~2 h behind a stuck job, i.e. no bound on a
  single probe).
- Read state through exit codes and single values (rules/git.md).
- Hook output is declarative, never imperative (rules/claude-code.md).

Out of scope: what the agent does while it waits.

## Native background, probed

The cheapest answer is the runtime's own run-in-background facility, if it
wakes the model when the command exits. Probed 2026-10-21:

| Runtime | Facility | Wakes the model on exit? |
|---|---|---|
| Claude Code | Bash `run_in_background` | Yes: a finished task re-invoked the headless session. Interactive not probed. |
| Codex 0.163.0 | "background terminal" (`/ps` to view, `/stop` to close) | No. The command ran to completion in an idle TUI and the model never started a turn. A `codex queue` doorbell at the command tail failed inside the sandbox ("failed to start embedded app server: Read-only file system"). |
| Pi 1.3.0 | None. Tools are read, bash, edit, write, subagent; `subagent` is synchronous. A plain `&` child survives `pi -p` exit but nothing wakes. | No facility |

Pi packages that add the missing facility exist (`pi-longrun`,
`pi-patty-bg-tasks`, `@mjakl/pi-processes`, `pi-bg-run`); they are listed in
`2026-10-21-longrun-language-audit.md`, read from their READMEs only and not
audited.

So an instruction to use the runtime's background facility is portable only in
its first half (launch with a deadline, do not block). The wake-up exists on
Claude Code alone. On Codex the model sees the result at its next turn, or via
`codex queue` once the registration question below is answered; on Pi it
needs an extension or this design. The waiter below is therefore the fallback
for two of the three runtimes, not a speculative extra.

## Design: one waiter, per-runtime doorbells

There is one mechanism, not a ladder of stages: a detached **waiter** that
records an **outcome**, and per-runtime **delivery** adapters that hand the
outcome to a model turn. A model is paid for only at delivery.

### Condition

A command that answers in exit codes: 0 satisfied, 2 / 126 / 127 never
satisfiable (126 and 127 mean the probe cannot run, so waiting is pointless),
anything else pending. It is stored as an argv array, never a shell string.

### Waiter (`idh-await`, a transient systemd user unit)

The backend is systemd. The waiter is a transient user service started with
`systemd-run --user`, named `idh-wait-<wait-id>.service`. Hosts without
systemd are out of scope until a need appears (open point).

What systemd supplies, so it is not rebuilt:

- **Detach and survival:** the unit is outside the agent's process tree and
  outlives the session.
- **Uniqueness:** a second start of the same unit name is refused, so
  registering the same wait twice cannot create two waiters.
- **Deadline:** `RuntimeMaxSec=<deadline>` bounds the whole wait.
- **Cleanup:** `--collect` removes the unit once it is inactive.
- **Waiter liveness:** the unit state replaces a waiter pid and start time.

What the unit runs:

- `idh-await run`: loops the condition under `timeout` (the deadline bounds
  each probe, not only the loop) with backoff.
- **Registration-time check:** the first probe runs at registration, so a
  condition already satisfied (the job finished before the wait was
  registered) still yields exactly one outcome.
- Records exactly one **outcome**, by atomic rename: satisfied, failed or
  timed out, plus the probe's last line. The outcome is recorded, not
  recomputed: CI runs get superseded, merged branches get deleted, automerge
  gets disabled, so a later re-run can give another answer.
- `ExecStopPost=idh-await finish`: if no outcome exists when the unit stops,
  it writes one from `$SERVICE_RESULT`: `timeout` becomes timed out, anything
  else becomes failed (waiter died). A crashed waiter is thereby told apart
  from a real timeout.
- Only the waiter executes the condition, stored as an argv array. Hooks read
  `outcome.json` and nothing else, so write access to the state directory is
  not code execution.

### State and identity

Directory per wait:
`${XDG_STATE_HOME:-~/.local/state}/idh/waits/<runtime>/<session>/<wait-id>/`.

- `wait-id` = hash of (condition argv, target ref). It is also the unit
  name, so registering the same wait twice is refused by systemd and is
  idempotent. The deadline is fixed by the first registration.
- `wait.json`: owner pid and start time, runtime, session, deadline, argv.
  This file and `outcome.json` are a fixed interface: the Stopguard runner
  reads them into `Turn.live_waits` (see below), so a field rename is announced
  to that design first.
  The owner's liveness is checked by pid plus start time from
  `/proc/<pid>/stat` field 22; a bare pid is reused. The waiter's own
  liveness and takeover are systemd's.
- `outcome.json`: the one outcome.
- The waiter directory plus the unit is the registration; there is no separate
  record.

### Delivery: claim by rename

Every channel claims an outcome by renaming `outcome.json` to
`claimed.<channel>.json` in the same directory. One rename wins; the others
see "not found". This gives at-most-once delivery per claimant and no double
resume. A claimant that crashes leaves a `claimed.*` file that a sweep can
re-offer.

Channels, tried in order when the outcome lands:

1. **Live push** (owner alive).
   - Claude Code: the agent starts a tiny blocker as a background task that
     waits on `outcome.json` under the same deadline; its exit re-invokes the
     session.
   - Pi: an extension watches for the outcome and calls
     `sendMessage({triggerTurn: true})`, or `deliverAs: "followUp"` while a
     turn is streaming.
   - Codex: `codex queue --thread <id> --message <outcome>` (probed, see below).
2. **Resume** (owner dead). Gated on the owning process being gone, checked by
   pid plus start time, and on a per-session `flock` so two waiters never
   resume one session. Not gated on "idle": idleness is hard to detect, death
   is not.
   - `claude -p --resume <id> "<outcome>"`
   - Codex: the same `codex queue` command; the app-server daemon runs the
     turn. `codex exec resume` is not used.
   - `pi -p --session <id> "<outcome>"`
3. **Pull** (always available). The prompt-submit and session-start hooks
   claim any unclaimed outcome and state it declaratively. This is the floor
   on every runtime.

Live push lands at a tool-call boundary on every runtime: a notification
cannot interrupt a tool call in flight (stated limit of the Pi packages
surveyed; Claude Code's background-task re-invocation behaves alike). A long
foreground command delays delivery until it returns.

If the owner is alive and no live channel exists, the outcome waits for pull.
A resume against a live session would start a copy (Claude Code) or risk two
writers on one session (Codex, Pi: unverified).

### Lifecycle

- Waits clean themselves at the deadline: a timed-out outcome is recorded,
  claimed and removed like any other.
- A claimed outcome is removed once the claiming turn has started. A crash in
  between re-delivers, so the response step must be idempotent.
- A sweep (lair or molt) removes stale `claimed.*` files and waiter
  directories whose waiter and owner are both dead past deadline plus grace.
  The branch-cleanup rule (just-completed task only) governs branches, not
  these directories.
- "Abandoned" is not an outcome. An owner that has exited is the case the
  resume channel exists for; only a deleted or archived session record means
  nobody can be told.

## Runtime capabilities

VERIFIED offline (Opus review, 2026-10-21; Claude Code 2.1.306, Codex 0.163.0,
Pi 1.3.0):

- Claude Code: `--resume <id>`, `-p`, `--bg --resume <id>` (starts a copy
  when the session is running); `CLAUDE_CODE_SESSION_ID` and `CLAUDE_PID` in
  the shell env; hook names Stop, UserPromptSubmit, SessionStart, SessionEnd
  and `stop_hook_active` present in the binary; background Bash tasks
  re-invoke the session on exit. The adapter wires SessionStart, SessionEnd
  and PreToolUse only.
- Codex: `codex exec resume [SESSION_ID] [PROMPT]`; `codex queue --thread
  <id> --message <text>` ("queue a message for an existing session");
  hook names Stop, UserPromptSubmit, SubagentStop, `stop_hook_active` in the
  binary. The adapter wires SessionStart and PreToolUse only.
- Pi: `-p`, `--session <path|id>`; extension API `sendMessage(...,
  {triggerTurn, deliverAs: steer|followUp|nextTurn})`, `ctx.isIdle()`;
  events `agent_end`, `turn_end`, `input`, `before_agent_start`,
  `session_start`, `session_shutdown`; `PI_SESSION_ID` and `PI_SESSION_FILE`
  in the bash tool env. The adapter already injects via `deliverAs: "nextTurn"`.
- Host: `systemd-run`, `setsid`, `timeout` present; user linger on (this
  machine only).
- systemd 255 on this host, probed 2026-10-21 with scratch units (positive
  controls fired): `RuntimeMaxSec` stops the unit and `ExecStopPost` sees
  `SERVICE_RESULT=timeout`, `EXIT_CODE=killed`, `EXIT_STATUS=TERM`; a clean
  exit gives `success`, a non-zero exit `exit-code`, a SIGKILL of the main
  process `signal` (`EXIT_STATUS=KILL`); a second start of a running unit name
  is refused ("already loaded or has a fragment file"); with `--collect` a
  stopped unit is gone, and the name registers again; the unit sits in
  `app.slice` under the user manager, outside the launching shell's terminal
  scope, and stayed active after that shell exited. Not tested: an agent
  session ending (Claude Code, Pi).

PROBED 2026-10-21 on the real runtimes (Claude Code with haiku, Codex
`gpt-6.1-sol`, Pi with the local padme model; scratch directories, positive
controls fired):

- Claude Code: `CLAUDE_CODE_SESSION_ID` and `CLAUDE_PID` are in the Bash env.
  A transient systemd unit and a `setsid nohup` child both survive a clean
  `claude -p` exit. A plain `&` child makes headless `-p` hang until killed,
  and is then gone: use the unit, never a bare child. A background Bash task
  that finishes re-invokes the headless session (the final answer reported it).
  `claude -p --resume <id>` of an exited session works and keeps context.
- Codex: `CODEX_THREAD_ID` and `CODEX_SESSION_ID` are in the shell env. In a
  plain interactive TUI (`codex`, not through the daemon) `codex queue
  --thread <id> --message ...` starts a turn when the TUI is idle. On a closed
  thread the same command is accepted and the managed `codex app-server
  daemon` runs the turn itself and writes it to the session file. So `queue` is
  both the live and the resume channel, and it depends on that daemon.
  `codex exec resume` on a thread with an active writer (the open TUI, or the
  daemon after a queue) fails at once with "already has an active writer": a
  safe refusal. The default `codex exec` sandbox (workspace-write) blocks
  `systemd-run` ("Failed to connect to bus: Operation not permitted");
  `-s danger-full-access` starts the unit.
- Pi: `PI_SESSION_ID` and `PI_SESSION_FILE` are in the bash env. Children,
  including a plain `&` one, survived a `pi -p` exit. `pi -p --session <file>`
  of an exited session works. Against a session open in the TUI it did not
  refuse: it hung until the 120 s timeout and wrote nothing (cause not
  established).

Consequences for the design: Codex delivery is `queue` for both owner states,
so its separate resume command is dropped; the dead-owner gate stays mandatory
for Pi, where nothing else prevents a second writer; and registration from a
sandboxed Codex shell needs an answer (open point).

STILL UNVERIFIED:

- Whether `codex queue` works with no app-server daemon running.
- Whether a Codex sandboxed shell can write the wait state directory (not
  tested; workspace-write limits writes to the workspace and temp).
- Whether a Codex Stop hook can block or inject, and whether a Pi `agent_end`
  handler can keep a turn from ending (Stopguard's smoke tests cover the Stop
  and `agent_before_settle` blocks, headless only).
- Interactive session end: Claude Code and Pi were tested through `-p` exits
  only. Pi's changelog says shutdown kills tracked detached bash children; the
  unit should escape it, untested.
- `claude --resume` against a session open in a TUI (the CLI help says it
  starts a copy).
- Hook trust was skipped in the Codex TUI, so Codex hooks were not exercised.

## Sequence (author-hours, estimates)

| Step | Work | h |
|------|------|---|
| 1 | Waiter as a systemd unit, outcome file, claim-by-rename, owner pid plus start time, registration-time check, pull hooks on all three runtimes | ~3 |
| 2 | Remaining probes (STILL UNVERIFIED list); the systemd and main runtime probes are done | ~0.5 |
| 3 | Live push: Claude doorbell ~0.5, Pi extension ~1, Codex queue ~0.5 | ~2 |
| 4 | Resume channel for a dead owner on all three runtimes, with the session flock | ~1.5 |

What each step leaves broken:

- After 1: nothing wakes on any runtime. The outcome is correct and appears on
  the next prompt or session start everywhere: no false "done", no polling, no
  unbounded wait, but no notification either.
- After 2: no code change; the UNVERIFIED list is decided.
- After 3: live Claude Code, Codex and Pi sessions wake; Codex without its
  app-server daemon stays on pull. A session that exited before the outcome
  does not wake on Claude Code or Pi.
- After 4: exited Claude Code and Pi sessions resume (Codex already did,
  through `queue`). A Codex session without the daemon stays on pull. A machine reboot before the
  outcome kills the waiter; persistence across reboot is not designed.

## Relation to Stopguard

The end-of-turn hook is one implementation, owned by
`conception/2026-10-21-stopguard-design.md` (section 6, "Relation to the
await-external design"). It supersedes the former step 5 of this sequence. Its
runner reads the wait registry above into `Turn.live_waits`, so its rule
`check()` stays pure; `live_waits` is `None` until this waiter exists, and rule
2 then falls back to its `wake:` marker. State paths: waits under
`~/.local/state/idh/waits/`, Stopguard spool under
`~/.local/share/idh/stopguard/`.

## Open points

- Registering a wait from a sandboxed Codex shell. Probed (Fable, Codex
  0.163.0, `codex exec -s workspace-write`): the sandbox blocks AF_UNIX
  connects (so the user bus and any socket relay), `~/.local/state` and
  `$XDG_RUNTIME_DIR` are read-only, `/tmp` and the workspace are writable, and
  the sandbox has its own pid namespace (a pid recorded inside is
  meaningless). A project-local `.codex/rules/*.rules` allow rule
  (`prefix_rule(pattern=[...], decision="allow")`) made the matching command
  run unsandboxed and unprompted, and that process sees the host pid
  namespace, `CODEX_THREAD_ID`, and can write the state directory.
  Proposal: a user-level rule allowing `idh-await register`, whose argv
  allow-list refuses shells and accepts only listed probe executables, because
  the rule makes `register` run model-supplied argv unsandboxed. Owner pid is
  `$PPID` of the unsandboxed command. Without the rule, `register` fails on
  the bus error and the session stays on pull. Rejected: a trusted hook
  (per-user trust, unexercised), `danger-full-access` (widens the whole run),
  a file-drop with a `.path` unit (feasible, one more component, no security
  gain). Unverified: a user-level rules directory, the interactive TUI, bare
  command name matching. Moot if the runtime-native background route is
  adopted.

- systemd is Linux only. If macOS or WSL becomes a target, a `setsid` plus
  `timeout` fallback is needed, and with it the pid-and-start-time lock the
  unit currently replaces.
