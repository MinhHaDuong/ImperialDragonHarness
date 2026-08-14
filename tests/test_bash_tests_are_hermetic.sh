#!/usr/bin/env bash
# Guard (ticket 0359): a shell suite must spawn its bash children hermetically.
#
# BASH_ENV points every child bash at scripts/bash-env.sh, which re-runs the
# credential selection at child startup. A suite that spawns `bash -c` without
# clearing that path hands the child whatever the live harness loaded — so a
# failing assertion prints a real credential (two leaked into a terminal and a
# session transcript on 2026-07-27), and an inherited value silently masks the
# behaviour under test (green while testing nothing).
#
# Two remedies are accepted, both already in the tree:
#   * spawn hermetically — `env -i HOME=… PATH=… bash -c …`, every variable the
#     child needs passed explicitly (test_bash_env_keys_selection_explicit.sh);
#   * clear the loader for the whole suite — `export BASH_ENV=` before any
#     child runs (test_seat_runner.sh, which also unsets the ambient keys it
#     inherited at its own startup).
#
# This guard makes the choice mechanical across every tests/*.sh, discovered by
# glob so a newly added suite is covered without editing this file.
#
# It reports FILE NAMES and LINE NUMBERS only — never the offending text, never
# an environment value. A guard that echoed what it found would reproduce the
# defect it exists to prevent.
#
# See rules/coding-bash.md § "Unsetting a variable in the parent does not unset
# it in the child".
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$(basename "${BASH_SOURCE[0]}")"

fail=0
checked=0
spawners=0

# --- (0) runtime proof that the idiom this guard enforces actually works --------
# A static scan whose "all clear" is indistinguishable from "I never looked" is
# not a check, so run it first against a case known to be POSITIVE. The probe
# uses a FAKE sentinel loader — a throwaway script exporting a recognisable dummy
# — never a real key: verifying with the live credential is how the 2026-07-27
# leak happened a second time. Both probes assert on a presence BOOLEAN; neither
# ever prints what it found.
_SENTINEL_DIR="$(mktemp -d)"
trap 'rm -rf "$_SENTINEL_DIR"' EXIT
printf 'export HERMETIC_PROBE_0359=dummy-sentinel-value\n' > "$_SENTINEL_DIR/loader.sh"

# (0a) Positive control: the plain `HOME=… bash -c` form — what the four suites
# used before ticket 0359 — DOES receive whatever BASH_ENV injects at child
# startup. If this comes back empty the probe is broken, not the tree clean.
_probe_leaky="$(BASH_ENV="$_SENTINEL_DIR/loader.sh" HOME="$_SENTINEL_DIR" \
    bash -c 'printf "%s" "${HERMETIC_PROBE_0359:-}"')"
if [ -z "$_probe_leaky" ]; then
    echo "FAIL: (0a) positive control saw nothing — the BASH_ENV probe is broken, so this guard proves nothing" >&2
    exit 1
fi
echo "PASS: (0a) positive control — a non-hermetic child does inherit the loader"

# (0b) The enforced form: `env -i` clears BASH_ENV, so the same child startup
# injects nothing. This is the property every conversion relies on.
_probe_hermetic="$(BASH_ENV="$_SENTINEL_DIR/loader.sh" \
    env -i HOME="$_SENTINEL_DIR" PATH="$PATH" \
    bash -c 'printf "%s" "${HERMETIC_PROBE_0359:-}"')"
if [ -n "$_probe_hermetic" ]; then
    echo "FAIL: (0b) an 'env -i' child still inherited the loader — the enforced idiom does not hold here" >&2
    exit 1
fi
echo "PASS: (0b) an 'env -i' child inherits nothing from the loader"
unset _probe_leaky _probe_hermetic

# Emit the file's logical lines as "<first-lineno><TAB><code>", where:
#
#   * physical lines ending in a backslash continuation are folded into their
#     successor, so the `env -i …\` + `bash -c …` two-line form
#     (test_bash_env_keys_precedence.sh) is judged as the single command it is;
#   * quoted string content and trailing comments are removed, leaving only the
#     shell CODE. `bash -c` inside quotes is data, not an invocation — a grep
#     pattern (this guard, and its sibling meta-test), a failure message, or the
#     inner spawn of an already-hermetic outer `bash -c 'bash -c ":"'`, which
#     inherits the outer's cleared environment and needs no `env -i` of its own.
#
# Quote state resets at each logical line: the multi-line body of a `bash -c '…'`
# is then read as code, which can only add candidates, never hide one.
_logical_lines() {
    awk '
        function strip(s,    i, c, st, out, n, last) {
            st = 0; out = ""; n = length(s)
            for (i = 1; i <= n; i++) {
                c = substr(s, i, 1)
                if (st == 0) {
                    if (c == SQ) { st = 1; continue }
                    if (c == DQ) { st = 2; continue }
                    last = (out == "") ? "" : substr(out, length(out), 1)
                    if (c == "#" && (out == "" || last == " " || last == "\t")) break
                    out = out c
                } else if (st == 1) {
                    if (c == SQ) st = 0
                } else {
                    if (c == "\\") i++
                    else if (c == DQ) st = 0
                }
            }
            return out
        }
        BEGIN { SQ = sprintf("%c", 39); DQ = sprintf("%c", 34) }
        { line = $0
          if (buf == "") start = NR
          if (line ~ /\\[ \t]*$/) { sub(/\\[ \t]*$/, " ", line); buf = buf line; next }
          buf = buf line
          print start "\t" strip(buf)
          buf = "" }
        END { if (buf != "") print start "\t" strip(buf) }
    ' "$1"
}

for f in "$TESTS_DIR"/test_*.sh; do
    b="$(basename "$f")"
    [ "$b" = "$SELF" ] && continue
    checked=$((checked + 1))

    # Suite-wide remedy: `export BASH_ENV=` (to empty) disarms the loader for
    # every child this suite spawns, so its spawns need no per-call `env -i`.
    if grep -qE '^[[:space:]]*export[[:space:]]+BASH_ENV=[[:space:]]*(#.*)?$' "$f"; then
        spawners=$((spawners + 1))
        echo "PASS: $b (clears BASH_ENV suite-wide)"
        continue
    fi

    bad=""
    spawns=0
    while IFS=$'\t' read -r lineno text; do
        # `bash -c`, `bash -lc`, `bash -ec`: any child shell running a command
        # string. Other `bash …` forms take a script path and are out of scope.
        [[ "$text" =~ bash[[:space:]]+-[a-z]*c ]] || continue
        spawns=$((spawns + 1))
        [[ "$text" == *"env -i"* ]] && continue
        bad="${bad:+$bad,}$lineno"
    done < <(_logical_lines "$f")

    [ "$spawns" -gt 0 ] && spawners=$((spawners + 1))

    if [ -n "$bad" ]; then
        echo "FAIL: $b — non-hermetic bash child spawn at line(s) $bad (needs 'env -i' or a suite-wide 'export BASH_ENV=')" >&2
        fail=$((fail + 1))
    elif [ "$spawns" -gt 0 ]; then
        echo "PASS: $b ($spawns hermetic spawn(s))"
    else
        echo "SKIP: $b (spawns no bash child)"
    fi
done

if [ "$checked" -eq 0 ]; then
    echo "FAIL: no tests/test_*.sh found — guard has nothing to protect" >&2
    exit 1
fi
if [ "$spawners" -eq 0 ]; then
    echo "FAIL: no suite spawns a bash child — guard is vacuous, check its detection" >&2
    exit 1
fi
if [ "$fail" -ne 0 ]; then
    echo "GUARD FAILED: $fail of $checked shell suite(s) spawn bash children non-hermetically" >&2
    exit 1
fi
echo "OK: all $checked shell suite(s) spawn bash children hermetically ($spawners spawner(s))"
