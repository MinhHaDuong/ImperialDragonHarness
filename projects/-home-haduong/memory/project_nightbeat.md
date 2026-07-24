---
name: Nightbeat deployment
description: Live nightbeat timer on padme — config values, monitoring commands, timeout chain
type: project
originSessionId: f66e55c9-026e-404f-b730-645154cd3bf4
---
`claude-nightbeat.timer` is **live on padme** (enabled since 2026-04-25).

Schedule: hourly 22:00–06:00 weeknights; all 24h on weekends. RandomizedDelaySec=300.
Unit files: `~/.config/systemd/user/claude-nightbeat.{timer,service}`
Launcher: `~/.claude/scripts/beat.py` — Python orchestrator, rotates across 4 projects per invocation.

**Project rotation:** aedist-technical-report → cadens → Climate_finance → fuzzy-corpus (round-robin via counter at `~/.claude/logs/nightbeat/.run-counter`).

**Timeout chain (beat.py):**
- `PICK_TICKET_TIMEOUT_S=480` (8 min)
- `HOUSEKEEPING_TIMEOUT_S=600` (10 min)
- `ORCHESTRATOR_TIMEOUT_S=1800` (30 min)
- `systemd TimeoutStartSec=3420` (57 min) — hard last resort; SIGTERM trap writes `aborted` record

**Budget limits:** housekeeping=$0.25, pick-ticket=$0.50, orchestrator=$5.00

**State per project:** `beat-log.jsonl` in project root — one JSON record per line, newest last.
Fields: `last_run_at`, `ticket_id`, `branch`, `PR`, `outcome`, `diagnostics`, `duration_s`.

**Per-run logs:** `~/.claude/logs/nightbeat/YYYYMMDDTHHMMSSZ.log` (last 60 retained).

**Monitoring:**
```bash
# Live journal
journalctl --user -u claude-nightbeat.service -f

# Last beat result per project
jq -cs 'last' ~/cadens/beat-log.jsonl ~/aedist-technical-report/beat-log.jsonl \
  ~/Climate_finance/beat-log.jsonl ~/fuzzy-corpus/beat-log.jsonl

# Today's run summaries from log files
for f in ~/.claude/logs/nightbeat/$(date -u +%Y%m%d)T*.log; do
  grep -m1 "project slot\|beat done\|beat aborted" "$f" | head -2
done
```
