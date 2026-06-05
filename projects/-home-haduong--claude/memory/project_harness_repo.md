---
name: Harness repo setup
description: ImperialDragonHarness repo is installed at ~/.claude with daily auto-pull via systemd timer
type: project
originSessionId: 649d7dac-5143-47f9-8bdb-c822dc241ada
---
~/.claude/ is a git repo tracking https://github.com/MinhHaDuong/ImperialDragonHarness.

**Why:** The harness (rules, skills, hooks, commands, docs) needs version control and cross-machine sync.

**How to apply:** Changes to harness files should be committed and pushed to this repo. A systemd timer pulls once per day. The .gitignore uses a whitelist pattern — only harness components are tracked; runtime files (sessions, cache, credentials) are excluded. Each machine needs one source line in ~/.bashrc pointing at scripts/shell-init.sh (see README step 3).
