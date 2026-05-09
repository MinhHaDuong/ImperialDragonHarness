# Harness rules — index

Lightweight pointer table injected at session start. Read individual
files on demand when their scope signal applies to your task.

| File | Scope | Summary |
|------|-------|---------|
| [workflow.md](./workflow.md) | always | Session start gate, escalation protocol, when to ask the author, subagent and compaction rules. |
| [git.md](./git.md) | always | Branch discipline, commit-message standards, worktree lifecycle, merge-request workflow. |
| [state.md](./state.md) | skill-list: `/end-session` | STATE.md format spec — sections, length cap, pruning rules. |
| `tickets/AGENTS.md` (project-level) | skill-list: `ticket-*`, `new-ticket`, `start-ticket` | Ticket format rules injected via `@tickets/AGENTS.md` in project CLAUDE.md — no global rules file needed. |
| [coding-python.md](./coding-python.md) | condition: project contains `*.py` (or `pyproject.toml` / `setup.py`) | Python 3.10+ style, testing markers, Make rules, `uv` workflow. |

Compliance is verified ex post by the `verify-adherence` skill — this
index is the single source of truth on when each rule file applies.
