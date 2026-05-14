---
name: ticket-close
description: Close a local ticket.
disable-model-invocation: false
user-invocable: true
argument-hint: <ticket-id> [reason]
---

# Close ticket $ARGUMENTS

Run:
```bash
~/.claude/skills/ticket-close/ticket-close-impl $ARGUMENTS
```

**Behavior**:
- Closes the ticket and commits the change
- Detects if the branch contains only erg file changes
- For erg-only branches: attempts fast-forward push to origin/main (bypasses PR)
- For non-erg branches or if push fails: returns non-zero (caller should create PR)
- If script exits 0, ticket is already merged; if non-zero, PR path should be used
