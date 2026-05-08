---
paths:
  - "tickets/"
  - "tickets/spec-erg-v1.md"
last-reviewed: 2026-05-08
---

# Ticket log conventions — %erg v1

Tickets live in `tickets/` as `.erg` files. The log section is append-only.
Validate with `tickets/erg check tickets/`.

Format and base verbs: see `tickets/AGENTS.md`.

## Bump categories

| Category | Meaning |
|----------|---------|
| `permission` | Harness blocked a tool call awaiting user approval |
| `author-decision` | Agent judged a call non-autonomous and stopped |
| `test-failure` | `make` / pytest / CI failed and blocked progress |
| `verify-reroll` | `/verify-gate` returned REROLL or ESCALATE |
| `circuit-breaker` | Orchestrator killed the agent (timeout, ping-pong, redirect ban) |

## When to emit bump vs note

- Use **`bump`** when the agent stopped and waited for a human signal — a real pause in autonomous flow.
  The category distinguishes trivial stoppages (permission, circuit-breaker) from hard ones (author-decision, test-failure).
- Use **`note`** for informational annotations that do not represent a stoppage.

Write bump lines to the main-repo ticket file at `~/.claude/tickets/{ticket}.erg`,
not to any worktree copy.

## Cross-worktree concurrency

The branch is the WIP signal: start work by creating a branch whose name
contains the ticket ID. No claim/release protocol — concurrent sweeps may
pick the same ticket and diverge onto different branches; the merge sorts
it out. Do not reintroduce a local lockfile.
