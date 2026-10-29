# Raid log and sitrep

**Path.** `python3 "$IDH_ROOT/scripts/raid_log.py" path` prints it:
`$IDH_RAID_LOG`, else `<git common dir>/idh-raid/raid.log`. One file per
repository, shared by every worktree, untracked, append-only, and it survives
worktree removal. Write with
`python3 "$IDH_ROOT/scripts/raid_log.py" append EVENT raid=<id> key=value ...`; each line
is `<epoch> EVENT raid=<id> key=value ...`, values without spaces.

**Raid id.** Every line carries `raid=<id>`, so raids running at once in one
repository do not mix. `append RAID_START ...` mints a short random id (or takes
`raid=<id>` if given) and prints the line; read the id there and pass `raid=<id>`
on every later append. An append without `raid=` is refused (exit 2). Keep the
id in the command text, not in an environment variable: shell exports do not
persist across calls and the armed sitrep `--cmd` must carry it.
Lines without `raid=` (written before the field existed) belong to no raid and
are ignored by the sitrep.

| Event | Written | Fields |
|---|---|---|
| `RAID_START` | at raid start | `raid=` (minted when absent), optional `deadline=<epoch>` (set only when the author gave the raid a time budget), optional `gate_max=<seconds>` (default 1800) |
| `WAVE_BASE` | Phase 4, and each refresh | `sha=` |
| `WAVE` | when a wave launches | `n=`, `tickets=a,b` |
| `PR` | every step change of a PR | `n=`, `ticket=`, `step=` (`executing`, `gaze`, `gate_round_N`, `merged`, `escalated`) |
| `BREAKER` | when a circuit breaker fires | `kind=`, `ticket=` |
| `QUEUE` | after each wave plan and merge | `n=` tickets still waiting |
| `SITREP` | written by `raid-sitrep.py` | `raid=` (only; the `--raid` value) |

**Reading.** `python3 "$IDH_ROOT/scripts/raid-sitrep.py" --raid <id>` reads only
that raid's lines (a missing `--raid` prints `UNREADABLE raid`; an id with no
`RAID_START` line prints `UNREADABLE RAID_START`; both exit 2) and renders elapsed time
(against the budget when `deadline=` is set; otherwise elapsed alone, no budget claimed), the latest wave, each PR's step, breakers logged since the
last `SITREP` line, live gate heartbeats (from `raid_gate_state`, so breaker
readings are not re-derived), and open PRs from the forge. A garbled or missing
line, a failed git or forge read, prints `UNREADABLE <part>` and exits 2: treat
that as "could not look", never as a clear. Its last line is the next action:

- `NEXT wait`: tickets are in flight.
- `NEXT resume wave`: nothing in flight, queue not empty. Launch the next wave
  now; do not end the turn.
- `NEXT wrap-up`: nothing in flight, queue empty. Go to Wrap up.

**Wake sources.** Every timed wake goes through
`python3 "$IDH_ROOT/scripts/runtime.py" wake arm --after <s> --cmd "<cmd>"` (ticket 1311): after
`<s>` seconds it runs `<cmd>` and wakes the session with `<cmd> exited <rc>: <output>`. `<cmd>`
runs later in a fresh bash, so expand `$IDH_ROOT` when arming (double-quote `--cmd`); a
`<cmd>` with its own quotes or `$` goes in through a quoted heredoc, as the merge skill's
queued-merge wait does. Read its one-line answer:

| Answer | Meaning | What the session does |
|---|---|---|
| `RUN-IN-BACKGROUND <command>` | Claude Code: only the session's own tool can start the process whose exit wakes it | run `<command>` as a background command |
| `ARMED codex <unit> ...` | Codex: a `systemd-run --user` timer will `codex queue` the result into the thread (queued, not proven delivered) | nothing; the turn starts when it arrives |
| `ARMED pi ...` | Pi: the result goes to the session's wake inbox; the `idh-wake` extension delivers it as a user message once the agent is idle (within a few seconds) | nothing |
| `NOOP wake arm <runtime>: <reason>` (exit 1) | no timed wake here: headless, no `systemd-run`, extension not loaded | sitrep at each wave boundary and breaker event |
| exit 3 | the runtime cannot be told (no marker, or two) | rerun with `--runtime <name>` |

`python3 "$IDH_ROOT/scripts/runtime.py" can wake` asks the same question without arming.
When `can wake` answers 1, use `notify` to reach the author:
`python3 "$IDH_ROOT/scripts/runtime.py" notify --key raid-<id> --title "raid <id>" --body "<what needs you>"`
(desktop popup where `notify-send` exists, plus an alert file under the git common dir;
a repeat of the same key within an hour prints `SUPPRESSED`).
Where no timed wake exists, say so in the first sitrep: "timed sitrep cadence
unavailable on this runtime; sitreps at wave boundaries only". The author's own
shell can still run `watch -n 900 python3 "$IDH_ROOT/scripts/raid-sitrep.py" --raid <id>`
on any runtime.
