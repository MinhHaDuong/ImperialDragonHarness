---
name: stats-cache.json telemetry source
description: ~/.claude/stats-cache.json contains full daily usage history — free checkpoint for all Claude Code surfaces
type: reference
---

`~/.claude/stats-cache.json` stores the data behind `/stats`:
- `dailyActivity[]`: messages, sessions, tool calls per day
- `dailyModelTokens[]`: tokens per model per day
- `modelUsage{}`: all-time totals per model (input/output/cacheRead/cacheCreate)
- `hourCounts{}`: session start distribution by hour
- `longestSession`, `totalSessions`, `totalMessages`

Updated when `/stats` is opened interactively, not continuously.
Daily granularity only — no per-hour or per-minute breakdown.

Daily snapshots via cron: `~/.claude/telemetry/snapshots/YYYY-MM-DD.json`
