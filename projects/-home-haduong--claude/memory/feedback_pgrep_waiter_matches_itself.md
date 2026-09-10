---
name: feedback-pgrep-waiter-matches-itself
description: "An `until pgrep -f \"<cmd>\"` waiter matches its own command line and never exits — and it outlives the session, reparented to init where nothing sweeps it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aceca52d-6c71-4a74-ae75-85a9b713e441
  modified: 2026-09-10T07:20:00.000Z
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

**It does not die with the session** (measured 2026-09-10). One of these was
still looping the next morning: **14 h 57**, its `make check` long finished, its
session gone, its worktree deleted under it, reparented to `systemd --user`.
That is the part the first draft of this note got wrong by omission — it framed
the cost as several turns of polling, so the reader pictures something that ends
when the conversation does. Nothing ends it but a `kill` or a reboot, and
nothing looks for it: the worktree GC reads live cwds only to *protect* a
worktree that still exists, and the scratch sweep keys on session directories,
not on processes.

Found by accident, while checking who was holding the worktrees during an
unrelated cleanup. So the detector is now `orphan_processes` in
`scripts/project-state.py`, surfaced as healthcheck check 13: a live process
whose cwd is a *deleted* worktree. That signal is narrow on purpose — "the
session that owns this process is dead" is not decidable, "this process sits in
a directory that no longer exists" is one `readlink` — and it was true of every
specimen.

Two details that cost a step each: `readlink /proc/<pid>/cwd` returns the path
with a literal `" (deleted)"` suffix, which is the whole signal; and killing the
waiter leaves its `sleep` child alive, so kill the children too.
