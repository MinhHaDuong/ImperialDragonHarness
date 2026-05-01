---
name: ticket-ready
description: List local tickets that are ready for work (unblocked).
disable-model-invocation: false
user-invocable: true
argument-hint:
---

# List ready tickets

## Steps

1. Run the CLI to list ready tickets:
   ```bash
   tickets/tools/go/erg ready tickets/ --json
   ```
   Returns JSON: `[{"id":"0013","title":"...","file":"..."},...]`
   The command handles Blocked-by resolution.

2. Display ready tickets (unblocked).

## Fallback (if erg binary is absent)

If `tickets/tools/go/erg` does not exist, degrade gracefully:

1. Read all `tickets/*.erg` files.

2. For each ticket with `Status: open`:
   - Check every `Blocked-by` reference:
     - Local ID (4 digits): look up the referenced ticket's status. Ready only if `closed`.
     - `gh#N`: treat as satisfied (no network call).
     - Missing reference: warn, treat as satisfied.

3. Display ready tickets (unblocked).
