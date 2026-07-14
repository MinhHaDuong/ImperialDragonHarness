---
name: feedback_bash_env_tests_real_invocation_path
description: "A BASH_ENV / hook script must be tested by spawning a real subprocess with the true trigger, not by sourcing it in the current shell — re-entry, ambient inheritance, and export-boundary bugs live only on the real path."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a645ef77-f8e4-4301-bc40-961e61b43b5b
---

Tests that `source scripts/bash-env.sh` in the *current* shell are blind to the entire class of bug that lives on the real BASH_ENV path. Three security defects in the `KEYS=provider:SRC=DST` explicit-selection code all passed the unit suite and were caught only by gaze's runtime review:

- **Fork bomb** — the selection subshell inherited `BASH_ENV=scripts/bash-env.sh`, so spawning `bash` re-sourced the script, which re-hit the selection entry, which spawned another `bash`… unbounded.
- **Ambient-env leak** — the subshell inherited the parent's exported environment, so indirect expansion could bind any already-exported variable, not just the intended provider key.
- **Guard forge** — a renamed export *target* (`provider:SRC=DST` where DST is a critical name) was not on the denylist, letting an untrusted file set `GCONV_PATH`/`LD_PRELOAD`/`BASH_ENV` etc. through the rename path.

**Why the suite missed all three:** sourcing in the current shell never re-enters via BASH_ENV, never crosses a process boundary, and inherits the test's own env — exactly the three surfaces the bugs occupy. The fix was `env -i bash -c` (drop BASH_ENV, start from an empty env) plus a denylist of process/interpreter-critical names.

**How to apply:** for any script invoked via BASH_ENV or a shell hook, the test must spawn a subprocess with the *real* trigger — `env -i HOME=… BASH_ENV=<script> PWD=<crafted-project-dir> bash -c …` — and assert on the resulting environment/behavior. A source-in-current-shell test cannot see re-entry, ambient inheritance, or export-boundary leaks. This is the env-injection-script specialization of the standing "fidelity checks pass what runtime breaks" insight; see also [[feedback_harness_is_the_deliverable]] and [[project_bash_env_secret_loading]]. (bash-env.sh KEYS hardening, PRs #599/#604, 2026-07-14)
