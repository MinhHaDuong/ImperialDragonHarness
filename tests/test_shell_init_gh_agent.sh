#!/usr/bin/env bash
# Ticket 1284: the codex and pi wrappers in scripts/shell-init.sh launch the
# runtime with GH_CONFIG_DIR set for the child only, when the agent gh config
# exists. Hermetic: stub runtimes print what they see.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INIT="$REPO/scripts/shell-init.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

FAIL=0
report() {
    printf '%-58s %s %s\n' "$1" "$2" "${3:-}"
    [ "$2" = PASS ] || FAIL=$((FAIL + 1))
}

mkdir -p "$TMP/bin" "$TMP/cwd"; cd "$TMP/cwd"
for r in codex pi claude; do
    printf '#!/bin/sh\nprintf %%s "${GH_CONFIG_DIR-<unset>}"\n' > "$TMP/bin/$r"
    chmod +x "$TMP/bin/$r"
done

# run HOME CALLER_GH "child cmd" -> child output, then "|" and the parent's value
run() {
    local home="$1" pre="$2" cmd="$3" envs=()
    [ -z "$pre" ] || envs=(GH_CONFIG_DIR="$pre")
    env -i HOME="$home" PATH="$TMP/bin:$PATH" IDH_SKIP_VALIDATE=1 "${envs[@]}" \
        bash -c '. "$1" 2>/dev/null; out=$($2); printf "%s|%s" "$out" "${GH_CONFIG_DIR-<unset>}"' _ "$INIT" "$cmd"
}

H1="$TMP/h1"; mkdir -p "$H1/.config/gh-agent"; : > "$H1/.config/gh-agent/hosts.yml"
H2="$TMP/h2"; mkdir -p "$H2/.config/gh-agent"
for r in codex pi; do
    got="$(run "$H1" "" "$r")"
    [ "$got" = "$H1/.config/gh-agent|<unset>" ] \
        && report "1. $r child gets agent config, parent stays clean" PASS \
        || report "1. $r child gets agent config, parent stays clean" FAIL "got: $got"
    got="$(run "$H2" "" "$r")"
    [ "$got" = "<unset>|<unset>" ] \
        && report "2. $r: no hosts.yml, nothing set" PASS \
        || report "2. $r: no hosts.yml, nothing set" FAIL "got: $got"
    got="$(run "$H1" /custom "$r")"
    [ "$got" = "/custom|/custom" ] \
        && report "3. $r: caller-set GH_CONFIG_DIR wins" PASS \
        || report "3. $r: caller-set GH_CONFIG_DIR wins" FAIL "got: $got"
done

got="$(run "$H1" "" "claude")"
[ "$got" = "<unset>|<unset>" ] \
    && report "4. claude wrapper untouched" PASS \
    || report "4. claude wrapper untouched" FAIL "got: $got"

[ "$FAIL" -eq 0 ]
