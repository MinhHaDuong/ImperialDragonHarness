---
name: feedback-pgrep-waiter-matches-itself
description: "An `until pgrep -f \"<cmd>\"` waiter matches its own command line and never exits — wait on a PID or a marker in the output file"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aceca52d-6c71-4a74-ae75-85a9b713e441
  modified: 2026-09-09T16:38:57.757Z
---

`until [ -z "$(pgrep -f 'make check')" ]; do sleep 10; done` never terminates.
The waiting shell's own command line contains the string `make check`, so
`pgrep -f` matches it: the loop waits for itself.

**Why it matters beyond the hang:** the symptom is not an error. On 2026-09-09
five such waiters accumulated, `pgrep -c` reported nine processes, and the
obvious reading — "the suite is still running, and slowly" — was wrong in a way
that cost several turns of polling before `ps -o args` showed the waiters
quoting themselves. A stuck waiter looks exactly like a slow job.

**How to apply:** wait on something that cannot describe itself.

```bash
# WRONG — the waiter's own argv matches
until [ -z "$(pgrep -f 'make check')" ]; do sleep 10; done

# CORRECT — a PID, captured before waiting
until ! kill -0 "$PID" 2>/dev/null; do sleep 10; done

# ALSO CORRECT — a marker the job writes when it ends
until grep -qE "passed|failed" "$OUTPUT"; do sleep 15; done
```

Better still in this harness: `run_in_background` and let the completion
notification arrive, or `Monitor` with one of the two correct forms above. Both
avoid the loop entirely.
