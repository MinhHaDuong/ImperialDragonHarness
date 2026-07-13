<!-- last-reviewed: 2026-06-09 -->
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

## General `set -euo pipefail` discipline

- Every script starts with `set -euo pipefail` unless there is an explicit reason not to.
- Functions that intentionally return non-zero use `return 0` explicitly or are called with `|| true` at the call site.
- Pipe chains: if a failing middle stage is acceptable, isolate it: `result=$(cmd1 | cmd2) || true`.
