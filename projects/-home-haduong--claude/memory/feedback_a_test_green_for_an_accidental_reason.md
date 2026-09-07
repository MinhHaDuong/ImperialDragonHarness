---
name: feedback_a_test_green_for_an_accidental_reason
description: "Repairing a configuration gap can turn a green suite red — the test was passing because the environment happened to be empty, which is an all-clear meaning 'nothing to look at', not 'the thing is correct'"
metadata:
  type: feedback
---

The known failure is a check whose all-clear cannot be told from "I could not
look". There is a nastier sibling: an all-clear that cannot be told from
**"there was nothing to look at"**, which only appears once someone supplies
the thing.

Measured on 2026-09-07. Writing the correct harness-level `KEYS=` line into
`~/.claude/.env` — the fix for a credential that reached no shell — turned
`make check` red on `tests/test_guard_cd_primary_repo.sh`. That test pinned
`HOME` for its children and inherited everything else, `BASH_ENV` included, so
a fresh bash re-ran the loader under a synthetic home with no keystore and
wrote to stderr, against two assertions that stderr be empty. It had been green
for years because nobody had that line.

**The diagnostic move is a three-arm control.** Two arms cannot separate the
cause from the fix:

| arm | result |
|---|---|
| pre-fix, the new config present | 2 FAIL |
| pre-fix, the inherited variable scrubbed | 0 FAIL |
| post-fix, the config present | 0 FAIL |

The middle arm is the whole diagnosis: the repo did not change, the inherited
environment did. Without it you cannot distinguish "my fix works" from "my fix
changed the subject".

**How to apply:**
- After repairing any per-machine configuration, re-run the full suite before
  declaring the repair done. Expect the repair to expose tests, and treat what
  it exposes as a finding rather than as your fix being wrong.
- Fix the test, not the configuration. The configuration is now correct; the
  test was relying on its absence.
- Build the control in the tree the test lives in. A first attempt copied the
  pre-fix script to a temp dir where it could not resolve its own `$HOOK`, and
  reported 20 FAIL in *both* arms — identical failure in every arm measures
  nothing, and it looks like a strong red.
- Expect the repair and its fallout to be two tickets in causal order (here
  0873 then 0874). Cross-reference them, or a later reader meets the second
  failure with no explanation.

Related: [[feedback_bash_env_tests_real_invocation_path]],
[[feedback_enumerate_untracked_with_status_uall]],
[[feedback_boolean_probe_must_not_expand_the_value]].
