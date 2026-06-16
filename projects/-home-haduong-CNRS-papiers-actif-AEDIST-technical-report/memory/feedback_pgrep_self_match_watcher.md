---
name: feedback_pgrep_self_match_watcher
description: Background watcher loops that pgrep their own pattern self-match and never exit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff935929-6d74-4b27-a396-830f64808637
---

A background-shell watcher that polls `pgrep -f "make check"` (or any `pgrep -f
PATTERN` where PATTERN appears in the watcher's own command line) **self-matches
and loops forever**. The watcher's command text literally contains the string,
so `! pgrep -f "make check"` is never true and `kill -0 $(pgrep ... | head -1)`
targets a live sibling watcher. Two such shells survived 9h+ on this project,
matching each other and themselves; the `make check` they watched had died at
~17% and never wrote its `passed|failed|EXIT=` sentinel, so the log-sentinel
condition was also permanently false.

**Why:** A watcher that never exits is worse than no watcher — it never
re-invokes the agent, leaks a process across sessions, and `/clear` orphans it.

**How to apply:**
- Never gate a loop on `pgrep -f PATTERN` where PATTERN is a substring of the
  loop's own command. Match a PID you captured (`pgrep` the target *before*
  starting the watcher, then `kill -0 $PID`), or `pgrep -f` a pattern unique to
  the target (full path / a flag the watcher line doesn't carry).
- Pair the process check with a **timeout fallback** so a watched process that
  dies without writing its sentinel still releases the loop (`SECONDS`-based cap
  or a max-iteration counter).
- Prefer the harness Monitor tool / `run_in_background` task tracking over a
  hand-rolled `until … sleep` shell when the harness can notify on completion —
  see the memory index note on harness-tracked background work.
