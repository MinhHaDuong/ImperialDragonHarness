---
name: feedback_poller_elapsed_is_the_quantum
description: "A driver that sleeps between status polls reports its own poll interval, not the job — two builds differing by 44 493 passages both read 140,3 s"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e638f30e-5d01-4ff0-be22-bf1aac1cf0db
  modified: 2026-09-03T11:05:52.960Z
---

`bench/run_build.py` sleeps `--poll` seconds, then asks for status, and breaks on the
first poll that sees `done`. So its `elapsed_s` is the true build time **rounded up to
the next poll boundary**. At `--poll 20` the 300- and 1 200-item keyword builds — 44 493
passages apart — both reported **140,3 s**; the full library read 332,9 s at `--poll 30`
against **305,9 s** at `--poll 5` (2026-09-03, ticket 0120 action 1).

**Why:** the instrument's resolution is invisible in its output. A wall-clock figure
carries no unit of uncertainty, so a quantized reading looks exactly like a measurement,
and the tell only appears when two runs that must differ come back identical. Nothing
errors, and the number is plausible in isolation.

**How to apply:** before quoting a wall clock from a polling driver, ask what its poll
interval was and keep the quantum under ~2 % of the figure. Record the quantum *in the
artifact* so the caveat is machine-readable, and let a test refuse a coarse one — the
guard belongs beside the number, not in the prose. Two runs of known-different size
returning the same time is the positive control for this defect; a single run cannot
show it. The same shape falsified a SPEC.md §5.2.9 claim that timing the convergence
harness's existing 1 Hz status polls would yield a latency distribution "at no
additional cost": a poller that sleeps between calls measures the job's duration, never
the call's latency, so that series does not exist until the driver times each round trip.

Related: [[feedback_probe_needs_discriminating_control]],
[[feedback_verify_the_load_bearing_claim]], [[feedback_warm_runs_and_single_point_fits]].
