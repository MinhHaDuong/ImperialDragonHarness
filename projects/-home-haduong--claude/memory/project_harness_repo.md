---
name: Harness repo setup
description: ImperialDragonHarness repo is installed at ~/.claude with daily auto-pull via systemd timer
type: project
originSessionId: 649d7dac-5143-47f9-8bdb-c822dc241ada
---
~/.claude/ is a git repo tracking https://github.com/MinhHaDuong/ImperialDragonHarness.

**Why:** The harness (rules, skills, hooks, commands, docs) needs version control and cross-machine sync.

**How to apply:** Changes to harness files should be committed and pushed to this repo. A systemd timer pulls once per day. The .gitignore uses a whitelist pattern — only harness components are tracked; runtime files (sessions, cache, credentials) are excluded. Each machine is set up with `~/.idh/bin/idh install` (ticket 0987): it creates the manifest's links, links `~/.local/bin/idh`, enables the mammoth-audit timer, and splices the scripts/bashrc-loader.sh block into ~/.bashrc between its begin and end markers. A bare `source` line would skip silently when ~/.idh is gone, leaving claude/codex/pi unwrapped. Since 2026-09-29 doudou and padme carry the marked block; `idh install` has not yet been run for real on either.
