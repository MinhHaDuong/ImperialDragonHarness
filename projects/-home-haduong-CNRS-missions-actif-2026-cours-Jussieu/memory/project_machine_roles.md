---
name: Machine roles in user's IDH setup
description: Which hosts in the user's fleet run autonomous services (nightbeat, etc.) and which do not — laptop vs server distinction
type: project
originSessionId: 6bc66762-4ea9-46c7-9686-607d1938d97c
---
`padme` is the server: nightbeat (`claude-nightbeat.timer`) runs there overnight,
30-min cadence weeknights 22:00–06:00 + all day weekends.

`doudou` is a laptop. **No nightbeat there.** Only `claude-refresh.timer` (daily IDH pull)
and `claude-telemetry-prune.timer` are appropriate user-systemd units for laptops.

**Why:** Autonomous overnight services need uptime — laptops sleep, lids close, batteries die.
The user explicitly does not want nightbeat on doudou.

**How to apply:** When auditing "doudou setup" or any laptop host against upstream STATE.md's
`doudou setup` checklist, treat the `install nightbeat systemd units` item as **not applicable**
and flag only `~/.bashrc` source line + `erg` binary (PATH-level and per-project) as actionable.
For any new host, ask whether it's a laptop or a server before suggesting autonomous timers.
