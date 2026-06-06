---
name: beat
description: Run one autonomous work cycle on the current project — housekeeping, then pick a ticket, then execute it (housekeeping → pick-ticket → raid). One beat is the heartbeat unit of the overnight autonomous pipeline (nightbeat).
user-invocable: true
argument-hint:
---

Run one beat cycle on the current project and report the outcome.

```bash
BEAT_PROJECT=$(git rev-parse --show-toplevel) python3 ~/.claude/scripts/beat.py
```

Report the one-line summary printed to stdout by beat.py.
