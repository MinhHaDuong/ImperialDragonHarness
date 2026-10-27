#!/usr/bin/env bash
# Ticket 1196: agent shells (BASH_ENV loader) export GH_CONFIG_DIR, a path and
# not a secret, only when the agent gh config exists. Hermetic: env -i, crafted HOME.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOADER="$REPO/scripts/bash-env.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

FAIL=0
report() {
    printf '%-58s %s %s\n' "$1" "$2" "${3:-}"
    [ "$2" = PASS ] || FAIL=$((FAIL + 1))
}

probe() { # $1 = HOME; prints GH_CONFIG_DIR or <unset>
    env -i HOME="$1" PATH="$PATH" BASH_ENV="$LOADER" \
        bash -c 'printf %s "${GH_CONFIG_DIR-<unset>}"'
}

# 1. config present -> exported
H1="$TMP/h1"; mkdir -p "$H1/.config/gh-agent"
: > "$H1/.config/gh-agent/hosts.yml"
got="$(probe "$H1")"
[ "$got" = "$H1/.config/gh-agent" ] \
    && report "1. exported when hosts.yml exists" PASS \
    || report "1. exported when hosts.yml exists" FAIL "got: $got"

# 2. dir without hosts.yml -> absent
H2="$TMP/h2"; mkdir -p "$H2/.config/gh-agent"
got="$(probe "$H2")"
[ "$got" = "<unset>" ] \
    && report "2. absent when hosts.yml missing" PASS \
    || report "2. absent when hosts.yml missing" FAIL "got: $got"

# 3. no config at all -> absent
H3="$TMP/h3"; mkdir -p "$H3"
got="$(probe "$H3")"
[ "$got" = "<unset>" ] \
    && report "3. absent when no config dir" PASS \
    || report "3. absent when no config dir" FAIL "got: $got"

# 4. an author-set GH_CONFIG_DIR is not overridden
got="$(env -i HOME="$H1" PATH="$PATH" GH_CONFIG_DIR=/custom BASH_ENV="$LOADER" \
    bash -c 'printf %s "${GH_CONFIG_DIR-<unset>}"')"
[ "$got" = /custom ] \
    && report "4. explicit GH_CONFIG_DIR kept" PASS \
    || report "4. explicit GH_CONFIG_DIR kept" FAIL "got: $got"

# 5. no loader, no export (the author's interactive shell)
got="$(env -i HOME="$H1" PATH="$PATH" bash -c 'printf %s "${GH_CONFIG_DIR-<unset>}"')"
[ "$got" = "<unset>" ] \
    && report "5. no BASH_ENV, no export" PASS \
    || report "5. no BASH_ENV, no export" FAIL "got: $got"

[ "$FAIL" -eq 0 ]
