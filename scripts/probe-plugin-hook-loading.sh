#!/usr/bin/env bash
# Does a skills-directory plugin's hook actually fire? Three cases, measured.
#
# Ticket 0887. The Claude Code adapter question turns on one fact the docs
# state and this probe checks: a plugin at $HOME/.claude/skills/<name>/ loads
# with no marketplace, no install step and no --plugin-dir flag. Reading that
# in a manual is not the same as watching a hook fire, so this runs it.
#
# Case A is the probe's own positive control. If A does not fire, the probe
# could not look -- a "did not fire" on B or C then means nothing, and the
# script says so rather than reporting three silent negatives as findings.
#
#   A  personal scope, real directory      expected: FIRED
#   B  personal scope, through a symlink   expected: FIRED   (layout freedom)
#   C  project scope, headless (-p)        expected: did not fire (no trust)
#
# Each case runs `claude -p` in a throwaway HOME with a SessionStart hook whose
# whole job is to touch a marker file. Requires a working `claude` on PATH and
# whatever credential that install already uses; it sends one trivial prompt
# per case. Nothing is read from or written to the real harness.
set -euo pipefail

MODEL="${PROBE_MODEL:-claude-haiku-4-5-20251001}"
TIMEOUT="${PROBE_TIMEOUT:-150}"

command -v claude >/dev/null || { echo "probe: no 'claude' on PATH" >&2; exit 2; }

ROOT=$(mktemp -d)
trap 'rm -rf "$ROOT"' EXIT

# Write a minimal skills-dir plugin whose only component is a SessionStart hook.
make_plugin() {  # $1 = plugin dir, $2 = plugin name, $3 = marker path
    mkdir -p "$1/.claude-plugin" "$1/hooks"
    printf '{"name":"%s","description":"hook-loading probe","version":"0.0.1"}\n' \
        "$2" > "$1/.claude-plugin/plugin.json"
    cat > "$1/hooks/hooks.json" <<EOF
{"hooks":{"SessionStart":[{"matcher":"","hooks":[{"type":"command","command":"sh -c 'echo FIRED > \"$3\"'","timeout":10}]}]}}
EOF
}

# Run one case: throwaway HOME, throwaway cwd, one prompt. Answer FIRED or not.
run_case() {  # $1 = case HOME, $2 = case cwd, $3 = marker path
    rm -f "$3"
    ( cd "$2" && timeout "$TIMEOUT" env HOME="$1" claude -p 'say OK' \
        --model "$MODEL" >/dev/null 2>&1 ) || true
    [ -f "$3" ] && echo FIRED || echo "did not fire"
}

# A -- personal scope, plugin directory in place.
mkdir -p "$ROOT/a/home/.claude/skills" "$ROOT/a/work"
make_plugin "$ROOT/a/home/.claude/skills/probe-a" probe-a "$ROOT/a/marker"
A=$(run_case "$ROOT/a/home" "$ROOT/a/work" "$ROOT/a/marker")

# B -- personal scope reached through a symlink: does discovery follow it?
mkdir -p "$ROOT/b/home/.claude/skills" "$ROOT/b/work" "$ROOT/b/elsewhere"
make_plugin "$ROOT/b/elsewhere/probe-b" probe-b "$ROOT/b/marker"
ln -s "$ROOT/b/elsewhere/probe-b" "$ROOT/b/home/.claude/skills/probe-b"
B=$(run_case "$ROOT/b/home" "$ROOT/b/work" "$ROOT/b/marker")

# C -- project scope under -p, which never shows the workspace-trust dialog.
mkdir -p "$ROOT/c/home/.claude" "$ROOT/c/work/.claude/skills"
make_plugin "$ROOT/c/work/.claude/skills/probe-c" probe-c "$ROOT/c/marker"
C=$(run_case "$ROOT/c/home" "$ROOT/c/work" "$ROOT/c/marker")

printf '%-46s %s\n' \
    "A  personal scope, real directory" "$A" \
    "B  personal scope, through a symlink" "$B" \
    "C  project scope, headless (-p)" "$C"

if [ "$A" != FIRED ]; then
    echo
    echo "probe: case A did not fire, so this run could not look at all." >&2
    echo "       B and C above are not findings. Check that 'claude' runs" >&2
    echo "       headlessly here before reading anything into them." >&2
    exit 1
fi
