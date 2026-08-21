<!-- last-reviewed: 2026-08-14 -->
# Coding Rules — Bash

## Arithmetic under `set -e`

`((expr))` exits 1 when the expression evaluates to 0 (arithmetic false). Under
`set -e` this **aborts the script silently** — the most common trap is a counter
starting at 0:

```bash
# WRONG — ((FAIL++)) exits 1 when FAIL==0, killing the script under set -e
((FAIL++))

# CORRECT — always safe
FAIL=$((FAIL + 1))

# ALSO CORRECT — explicit no-op on false
((FAIL++)) || true
```

Use `VAR=$((VAR + 1))` in new code. The `|| true` form is accepted in existing code.

## Associative arrays under `set -u`

`${arr[$key]}` under `set -u` fails with "unbound variable" when the key is absent.
Use a default to guard the access:

```bash
# WRONG — aborts if $stem not in _TIMER_UNITS
if [ -z "${_TIMER_UNITS[$stem]}" ]; then ...

# CORRECT — empty string when key absent
if [ -z "${_TIMER_UNITS[$stem]:-}" ]; then ...
```

Always use `${arr[$key]:-}` (or `${arr[$key]:-default}`) when the key may not exist.

## Tab-delimited records drop empty fields in `read`

Tab is IFS *whitespace*, so `IFS=$'\t' read` collapses consecutive tabs: an
empty mid-record field silently shifts every later field left (bit
reviewers.sh roster parsing, 2026-07-13 — a seat kind with no endpoint/model
put the trial-ticket in the wrong variable).

```bash
# WRONG — l gets "g", t gets "" (the empty field vanished)
printf 'a\tb\t\tg\n' | while IFS=$'\t' read -r k v l t; do ...

# CORRECT — pipe is not IFS whitespace; empty fields survive
printf 'a|b||g\n' | while IFS='|' read -r k v l t; do ...
```

Records with possibly-empty middle fields need a non-whitespace delimiter
(`|`, `;`) or a placeholder value. Tab-delimited `read` is safe only when
every field is guaranteed non-empty or the empty field is last.

## A boolean predicate over a state that has more than two values

`systemctl is-active --quiet` looks like a yes/no question. It is not. A
`Type=oneshot` service is `activating` for the whole duration of its run — it
reaches `active` only once it has nothing left to do — and `is-active` exits **3**
on `activating`. So the naive test reports "nothing is running" exactly while
something is running, and it cannot report anything else:

```bash
# WRONG — false for a oneshot that is running, and for one that never ran
if systemctl is-active --quiet "$svc"; then echo running; fi

# CORRECT — read the state, then decide which values you meant
state="$(systemctl show "$svc" -p ActiveState --value 2>/dev/null || true)"
case "$state" in active|activating) echo running ;; esac
```

Cost, 2026-08-21 (padme): a freshly written deploy script announced "catch-up:
none — nothing was due" while restic was scanning 115 GiB. The message was
harmless in that direction; the danger was believing it and launching a second
restic over the first, whose `restic unlock` preamble would have removed the
running backup's lock.

The shape generalises past systemd. Before writing `if <cmd> --quiet`, ask how
many states the underlying thing has, and which of them the exit code folds
together. Exit codes are a two-value channel; most real state is not.

**A negative result is the default output of everything that fails silently** —
wrong flag, wrong path, permission denied, wrong predicate. So a check whose
"all clear" is indistinguishable from its "I could not look" is not a check;
`tickets/AGENTS.md` states the general form for forge queries. The remedy is
the same everywhere: run the check once against a case **known to be positive**
— a deliberately broken fixture, the real state while the defect is live, or a
mock that lies in the right direction — and only then trust its silence. In a
test suite, the case that earns its place is the one that fails against the old
code.

## General `set -euo pipefail` discipline

- Every script starts with `set -euo pipefail` unless there is an explicit reason not to.
- Functions that intentionally return non-zero use `return 0` explicitly or are called with `|| true` at the call site.
- Pipe chains: if a failing middle stage is acceptable, isolate it: `result=$(cmd1 | cmd2) || true`.

## BASH_ENV / hook scripts: test via a real subprocess, never source-in-shell

A script that runs through `BASH_ENV` (or any PreToolUse/PostToolUse hook) is
loaded by a *fresh* non-interactive `bash` on every subprocess. Its real
behaviour — re-entry when the subprocess itself inherits `BASH_ENV`, ambient-env
leakage across the `env -i` boundary, export-name collisions with the caller —
appears only in that invocation path. A test that `source`s the script into the
test's own shell is blind to all of it: three security defects (a `BASH_ENV`
re-entry fork bomb, an ambient-env leak, a guard-name forgery) passed the
source-in-shell unit suite and were caught only by runtime review (PRs
#599/#604, 2026-07-14).

Test such scripts by spawning a real, hermetic subprocess:

```bash
# WRONG — blind to re-entry, inheritance, and the export boundary
source scripts/bash-env.sh
[ "$SOME_VAR" = expected ] || exit 1

# CORRECT — the real load path, hermetic base env
out=$(env -i HOME="$tmphome" BASH_ENV="$PWD/scripts/bash-env.sh" \
        bash -c 'printf %s "$SOME_VAR"')
[ "$out" = expected ] || exit 1
```

`env -i` gives a known-empty base env (so an inherited variable can't mask a
bug), `HOME=` points at a crafted fixture, and `BASH_ENV=` exercises the exact
mechanism the caller triggers. Enforced by
`tests/test_bash_env_tested_via_subprocess.sh`.

### Unsetting a variable in the parent does not unset it in the child

`BASH_ENV` re-runs the loader — including its credential selection — at the
startup of *every* child bash. Whatever the parent set is overwritten:

```bash
# WRONG — the child gets the real value back from BASH_ENV
unset OPENAI_API_KEY
bash -c 'printf %s "$OPENAI_API_KEY"'    # prints the REAL key

# CORRECT — stop the loader from running in children
export BASH_ENV=
# or spawn hermetically
env -i HOME="$h" PATH="$PATH" bash -c '…'
```

**Assert against a child, never the current shell.** A parent-scope check
passes while the leak is alive, because re-injection happens at child startup;
that blind spot made a first attempt at this exact fix a silent no-op
(2026-07-27).

Two consequences, and the second is the one that bites quietly:

- **Disclosure.** A failing assertion prints what it found. When that is a live
  credential, the failure message *is* the leak — this spilled two real keys
  into a terminal and a session transcript.
- **False confidence.** An inherited variable masks the behaviour under test. A
  suite asserting "DST not set" was comparing against an ambient value unrelated
  to the code path: red for the wrong reason, and green-while-testing-nothing had
  the value happened to match.

Verify with a **fake sentinel** loader, never the real key: point `BASH_ENV` at
a script exporting a recognisable dummy, run the suite, and grep the output for
the dummy. Verifying with the real key is how you leak it a second time.
