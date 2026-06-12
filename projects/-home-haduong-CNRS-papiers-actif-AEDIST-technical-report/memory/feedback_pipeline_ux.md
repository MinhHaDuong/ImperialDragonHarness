---
name: Pipeline UX requirements
description: Long-running tasks need progress bars, circuit breakers, checkpointing, resumability, parallelism control
type: feedback
---

Long-running pipeline tasks (evaluate-all, query sweeps) must have:

1. **Progress bar or logging** — show which model is being processed, N/total, ETA
2. **Circuit breaker** — stop after N consecutive failures, configurable
3. **Checkpointing** — write results incrementally, not all-at-end
4. **Interruptability/resumability** — Ctrl-C safe, resume from where it stopped
5. **Controllable parallelism** — `--jobs N` flag, not hardcoded

**Why:** The user's time is the bottleneck. Batch operations on local JSON files should feel instant. When they can't be instant, they must show progress. Silent hangs are unacceptable.

**How to apply:** Every CLI script that processes multiple files gets a progress counter. Use `tqdm` or simple `log.info(f"{i}/{total}")`. Write results after each model, not in one batch at the end. Add `--jobs` flag for parallelism where applicable.
