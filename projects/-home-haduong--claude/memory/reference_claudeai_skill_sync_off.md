---
name: reference_claudeai_skill_sync_off
description: "claude.ai skill sync is off in Claude Code since 2026-10-01; the harness skills/ tree is the single source of the author's skills"
metadata:
  type: reference
---

`~/.claude/settings.json` (untracked) carries `"syncClaudeAiSkills": false` since 2026-10-01. Before that, 19 claude.ai skills (8 author uploads, 11 Anthropic directory/example) were listed in every session (~3.9k tokens) and invoked 0 times in 2,913 Claude Code transcripts (2026-06-10 to 10-01). The 8 uploads were merged into `skills/` (tracker 0992) and deleted on claude.ai by the author.

The sync cache lives in `skills/synced/<uuid>/` (gitignored, skipped by check-agnostic); its `manifest.json` `source` field separates author uploads (`plugin`, ids `skill_01…`) from `anthropic` / `anthropic-example`. Per-skill control without disabling sync: `skillOverrides` in settings (reported by the docs agent, not tried). A new skill for the author goes into `skills/`, never claude.ai.
