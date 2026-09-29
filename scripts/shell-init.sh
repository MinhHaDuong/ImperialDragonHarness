#!/usr/bin/env bash
# Harness shell init — sourced from ~/.bashrc through the loader in
# scripts/bashrc-loader.sh (which also covers the case where this file is
# unreachable).
#
# Wraps claude, codex and pi. Before each launch, the projection validator
# (scripts/validate-projections.py, ticket 0983) checks every link the runtime
# depends on and refuses the launch with the culprit and its repair: a
# dangling link would otherwise drop the guard or the instructions silently.
# The claude wrapper also skips permission prompts and names the session
# after the project.
#
# Bypass, explicit and logged: IDH_SKIP_VALIDATE=1 <runtime> ...

_idh_bypass_log() {
  local dir="${XDG_STATE_HOME:-$HOME/.local/state}/idh"
  mkdir -p "$dir" 2>/dev/null
  printf '%s %s bypass cwd=%s\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$1" "$PWD" \
    >>"$dir/validate-bypass.log" 2>/dev/null
  echo "idh: IDH_SKIP_VALIDATE=1, launching $1 without the projection check (logged to $dir/validate-bypass.log)" >&2
}

# _idh_preflight RUNTIME — 0 when the launch may proceed.
_idh_preflight() {
  if [ "${IDH_SKIP_VALIDATE:-}" = 1 ]; then
    _idh_bypass_log "$1"
    return 0
  fi
  local v="$HOME/.idh/scripts/validate-projections.py"
  if [ ! -f "$v" ]; then
    # ~/.idh vanished after this shell sourced the wrappers.
    local hint
    hint=$(cat "${XDG_STATE_HOME:-$HOME/.local/state}/idh/last-good-root" 2>/dev/null)
    echo "idh: refusing to launch $1: $v is unreachable, so $HOME/.idh no longer resolves to the harness checkout." >&2
    echo "  repair: ln -sfn ${hint:-/path/to/harness-checkout} $HOME/.idh" >&2
    echo "  To launch anyway (logged): IDH_SKIP_VALIDATE=1 $1 ..." >&2
    return 1
  fi
  python3 "$v" "$1"
}

claude() {
  _idh_preflight claude || return
  local name top
  top=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)
  name=$(basename "${top:-$PWD}")
  command claude --dangerously-skip-permissions --name "$name" "$@"
}

codex() {
  _idh_preflight codex || return
  command codex "$@"
}

pi() {
  _idh_preflight pi || return
  command pi "$@"
}
