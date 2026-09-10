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

Both were found by accident during an unrelated cleanup, and two in 43 hours of
uptime is the accumulation rate: the waiter is not a rare slip. 105 of these
were written in 101 days of transcripts, **every one of them by an agent, none
by the author**. Some show an agent that had already met the self-match and was
fighting it — `pgrep -c … -le 1` to tolerate one match, a double negation —
which is the tell that the defect is the shape, not the predicate.

**A detector for the corpse was built and dropped** (2026-09-10). It keyed on a
live process whose cwd is a *deleted* worktree, which held for the first
specimen and failed on the second, stranded in a scratchpad that still exists —
n=1 dressed as a rule. The signal that fits both is reparentation: a process
whose parent is init while its cwd sits under a session path. Kept here for
whoever builds the sweep; the mop was dropped because it does not close the tap.

**What closed the tap: a `PreToolUse(Bash)` guard**, `guard-pgrep-waiter.sh`,
denying the shape outright. Two instruments were tried and rejected first, and
the order is the lesson. A memory note — this one — had the correct recipe since
2026-09-09 and reached none of the 105, because memory is recalled by relevance.
A resident rule in `rules/workflow.md` was then written, and it would have
worked, but it cost 474 characters in every session of every project and
required raising a capped budget. Review found the cheapest instrument had never
been weighed: a script costs *zero* resident budget and blocks the mistake
structurally instead of hoping the prose is read. **Reach for the guard before
the rule before the note** — the three differ by orders of magnitude in both
cost and reliability, and the ranking is not the order they come to mind in.

Three details that cost a step each. `readlink /proc/<pid>/cwd` returns the path
with a literal `" (deleted)"` suffix. Killing the waiter leaves its `sleep`
child alive, so kill the children too (the 14 h 57 specimen had one; the
16 h 49 one did not). And a sweep that greps command lines for the waiter
*matches itself*, exactly like the waiter — which is why the guard requires
`sleep` alongside `pgrep` and a loop keyword, so that a command written to hunt
these waiters is not blocked by the guard against them. That fired for real,
against an earlier draft, in the session that wrote it.
