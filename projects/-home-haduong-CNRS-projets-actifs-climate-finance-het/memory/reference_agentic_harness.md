---
name: agentic-harness repo
description: Reusable AI agent workflow framework at ~/CNRS/code/agentic-harness — telemetry is the first module
type: reference
---

Repo: `MinhHaDuong/agentic-harness` (GitHub, public)
Local: `~/.agent/` (moved from `~/CNRS/code/agentic-harness` on 2026-03-26)

First module: `telemetry/` — usage tracking for Claude Code.
- `telemetry/bin/snapshot` — copies stats-cache.json to ~/.claude/telemetry/snapshots/
- `telemetry/bin/log-agent-metrics` — appends agent task notification data to events.jsonl
- `telemetry/bin/usage-report` — reads snapshots + events, prints summary
- `telemetry/bin/install-cron` — daily snapshot at 23:55

Future modules: hooks, runbooks, skills (extracted from Oeconomia project harness).

Note: HDMX-coding-agent needs collaborator access to push.
