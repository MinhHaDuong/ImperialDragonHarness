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
persist across calls and the background `sleep 900; sitrep` must carry it.
Lines without `raid=` (written before the field existed) belong to no raid and
are ignored by the sitrep.

| Event | Written | Fields |
|---|---|---|
| `RAID_START` | at raid start | `raid=` (minted when absent), `deadline=<epoch>`, `gate_max=<seconds>` |
| `WAVE_BASE` | Phase 4, and each refresh | `sha=` |
| `WAVE` | when a wave launches | `n=`, `tickets=a,b` |
| `PR` | every step change of a PR | `n=`, `ticket=`, `step=` (`executing`, `gaze`, `gate_round_N`, `merged`, `escalated`) |
| `BREAKER` | when a circuit breaker fires | `kind=`, `ticket=` |
| `QUEUE` | after each wave plan and merge | `n=` tickets still waiting |
| `SITREP` | written by `raid-sitrep.py` | `raid=` (only; the `--raid` value) |

**Reading.** `python3 "$IDH_ROOT/scripts/raid-sitrep.py" --raid <id>` reads only
that raid's lines (a missing `--raid` prints `UNREADABLE raid`; an id with no
`RAID_START` line prints `UNREADABLE RAID_START`; both exit 2) and renders elapsed time
against the budget, the latest wave, each PR's step, breakers logged since the
last `SITREP` line, live gate heartbeats (from `raid_gate_state`, so breaker
readings are not re-derived), and open PRs from the forge. A garbled or missing
line, a failed git or forge read, prints `UNREADABLE <part>` and exits 2: treat
that as "could not look", never as a clear. Its last line is the next action:

- `NEXT wait`: tickets are in flight.
- `NEXT resume wave`: nothing in flight, queue not empty. Launch the next wave
  now; do not end the turn.
- `NEXT wrap-up`: nothing in flight, queue empty. Go to Wrap up.

**Wake sources** (probed 2026-10-21, `conception/discussions/2026-10-21-await-external-design.md`):

| Runtime | Timed wake | Cadence |
|---|---|---|
| Claude Code | A background `sleep 900; sitrep --raid <id>` command exits and re-invokes the session | every 15 minutes, re-armed after each wake |
| Codex | Background terminals run but do not wake the model | none found: sitrep at each wave boundary and breaker event |
| Pi | No native facility (add-on packages unverified) | none found: sitrep at each wave boundary and breaker event |

Where no timed wake exists, say so in the first sitrep: "timed sitrep cadence
unavailable on this runtime; sitreps at wave boundaries only". The author's own
shell can still run `watch -n 900 python3 "$IDH_ROOT/scripts/raid-sitrep.py" --raid <id>`
on any runtime.
