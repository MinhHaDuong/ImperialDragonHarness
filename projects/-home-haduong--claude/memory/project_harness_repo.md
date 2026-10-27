---
name: Harness repo setup
description: ImperialDragonHarness lives at ~/.agents (installed by `idh install`); ~/.claude holds a stale clone and runtime state
type: project
originSessionId: 649d7dac-5143-47f9-8bdb-c822dc241ada
---
The canonical harness checkout is `~/.agents`, tracking https://github.com/MinhHaDuong/ImperialDragonHarness. `~/.claude/` still holds an older clone of the same repo (last commit 2026-10-01) next to Claude Code's runtime state; it is not where harness work happens.

**Why:** The harness (rules, skills, hooks, adapters, scripts) needs version control and cross-machine sync, and Claude Code's own directory is runtime state.

**How to apply:** Change harness files in a worktree of `~/.agents`, through a branch and PR; machines catch up via `scripts/sync-local-main.sh` (no daily-pull timer exists, checked 2026-10-27). Each machine is set up with `idh install` (`~/.local/bin/idh` → `~/.agents/bin/idh`, ticket 0987, run on padme 2026-10-27): it creates the manifest's links, puts the public `idh-*` commands on PATH (1249, 1264) and splices the bashrc-loader block between its markers. It installs no timer: the stale-skill audit is a harness-doctor measurement run on demand (`scripts/mammoth-audit.py`, 1264); the old `idh-mammoth-audit` user timer was removed from padme and doudou on 2026-10-27.
