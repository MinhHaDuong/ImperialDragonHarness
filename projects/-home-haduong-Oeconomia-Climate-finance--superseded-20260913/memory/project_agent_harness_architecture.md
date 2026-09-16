---
name: Agent harness architecture (.agent/ parallel to .claude/)
description: Harness lives in .agent/ at user and project level, .claude/ symlinks to it for non-Claude elements
type: project
---

The agentic harness (https://github.com/MinhHaDuong/agentic-harness) should install to `.agent/` directories, parallel to `.claude/`:

- `~/.agent/` — user-level: telemetry (log-celebration), cross-project memories, shared bin/
- `<project>/.agent/` — project-level: project-specific agent config, project telemetry
- `~/.claude/` symlinks to `~/.agent/` for non-Claude-specific elements
- `<project>/.claude/` symlinks to `<project>/.agent/` likewise

**Why:** Agent-agnostic — works with any AI agent, not just Claude. Avoids machine-specific paths like `~/CNRS/code/`. Separates user-level (cross-project) from project-level concerns.

**How to apply:** `log-celebration` and similar tools belong in the harness, not in individual project repos. Until the harness is set up, runbooks should gracefully skip telemetry steps.

Priority: high but blocked until after morning review, data paper release, mail, and weekly planning (as of 2026-03-25).
